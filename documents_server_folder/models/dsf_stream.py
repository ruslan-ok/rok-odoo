import base64
import contextlib
import os
import mimetypes
from io import BytesIO
from os.path import join as opj
from pathlib import Path
from zlib import adler32
from odoo.http import Response, request
from odoo.tools import config

try:
    from werkzeug.utils import send_file as _send_file
except ImportError:
    from odoo.tools._vendor.send_file import send_file as _send_file

# The cache duration for content where the url uniquely identifies the
# content (usually using a hash), one year.
STATIC_CACHE_LONG = 60 * 60 * 24 * 365


class DsfStream:
    """
    Send the content of a file, an attachment or a binary field via HTTP

    This utility is safe, cache-aware and uses the best available
    streaming strategy. Works best with the --x-sendfile cli option.

    Create a Stream via one of the constructors: :meth:`~from_path`:, or
    :meth:`~from_binary_field`:, generate the corresponding HTTP response
    object via :meth:`~get_response`:.

    Instantiating a Stream object manually without using one of the
    dedicated constructors is discouraged.
    """

    type: str = ''  # 'data' or 'path' or 'url'
    data = None
    path = None
    url = None

    mimetype = None
    as_attachment = False
    download_name = None
    conditional = True
    etag = True
    last_modified = None
    max_age = None
    immutable = False
    size = None
    public = False

    def __init__(self, **kwargs):
        # Remove class methods from the instances
        self.from_path = self.from_attachment = self.from_binary_field = None
        self.__dict__.update(kwargs)

    @classmethod
    def from_path(cls, path):
        is_abs = os.path.isabs(path)
        if not is_abs:
            raise FileNotFoundError("File not found: " + path)
        path = os.path.normpath(os.path.normcase(path))
        if not os.path.exists(path):
            raise FileNotFoundError("File not found: " + path)
        check = adler32(path.encode())
        stat = os.stat(path)
        return cls(
            type='path',
            path=path,
            mimetype=mimetypes.guess_type(path)[0],
            download_name=os.path.basename(path),
            etag=f'{int(stat.st_mtime)}-{stat.st_size}-{check}',
            last_modified=stat.st_mtime,
            size=stat.st_size,
            public=False,
        )

    @classmethod
    def from_binary_field(cls, record, field_name):
        """ Create a :class:`~Stream`: from a binary field. """
        data = record[field_name] or b''

        # Image fields enforce base64 encoding. Binary fields don't
        # enforce anything: raw bytes are fine, expected even.
        # People nonetheless write base64 encoded bytes inside binary
        # fields, and expect automatic decoding when read, crazy!
        with contextlib.suppress(ValueError):
            data = base64.b64decode(
                # Some libs add linefeed every X (where X < 79) char in
                # the base64, for email mime. validate=True would raise
                # an error for those linefeeds so stip them.
                data.replace(b'\r', b'').replace(b'\n', b''),
                validate=True,
            )

        return cls(
            type='data',
            data=data,
            etag=request.env['ir.attachment']._compute_checksum(data),
            last_modified=record.write_date if record._log_access else None,
            size=len(data),
            public=record.env.user._is_public()  # good enough
        )

    def read(self):
        """ Get the stream content as bytes. """
        if self.type == 'url':
            raise ValueError("Cannot read an URL")

        if self.type == 'data':
            return self.data

        with open(self.path, 'rb') as file:
            return file.read()

    def get_response(
        self,
        as_attachment=None,
        immutable=None,
        content_security_policy="default-src 'none'",
        **send_file_kwargs
    ):
        """
        Create the corresponding :class:`~Response` for the current stream.

        :param bool|None as_attachment: Indicate to the browser that it
            should offer to save the file instead of displaying it.
        :param bool|None immutable: Add the ``immutable`` directive to
            the ``Cache-Control`` response header, allowing intermediary
            proxies to aggressively cache the response. This option also
            set the ``max-age`` directive to 1 year.
        :param str|None content_security_policy: Optional value for the
            ``Content-Security-Policy`` (CSP) header. This header is
            used by browsers to allow/restrict the downloaded resource
            to itself perform new http requests. By default CSP is set
            to ``"default-scr 'none'"`` which restrict all requests.
        :param send_file_kwargs: Other keyword arguments to send to
            :func:`odoo.tools._vendor.send_file.send_file` instead of
            the stream sensitive values. Discouraged.
        """
        assert self.type in ('url', 'data', 'path'), "Invalid type: {self.type!r}, should be 'url', 'data' or 'path'."
        assert getattr(self, self.type) is not None, "There is nothing to stream, missing {self.type!r} attribute."

        if self.type == 'url':
            if self.max_age is not None:
                res = request.redirect(self.url, code=302, local=False)
                res.headers['Cache-Control'] = f'max-age={self.max_age}'
                return res
            return request.redirect(self.url, code=301, local=False)

        if as_attachment is None:
            as_attachment = self.as_attachment
        if immutable is None:
            immutable = self.immutable

        send_file_kwargs = {
            'mimetype': self.mimetype,
            'as_attachment': as_attachment,
            'download_name': self.download_name,
            'conditional': self.conditional,
            'etag': self.etag,
            'last_modified': self.last_modified,
            'max_age': STATIC_CACHE_LONG if immutable else self.max_age,
            'environ': request.httprequest.environ,
            'response_class': Response,
            **send_file_kwargs,
        }

        if self.type == 'data':
            res = _send_file(BytesIO(self.data), **send_file_kwargs)
        else:  # self.type == 'path'
            send_file_kwargs['use_x_sendfile'] = False
            if config['x_sendfile']:
                with contextlib.suppress(ValueError):  # outside of the filestore
                    fspath = Path(self.path).relative_to(opj(config['data_dir'], 'filestore'))
                    x_accel_redirect = f'/web/filestore/{fspath}'
                    send_file_kwargs['use_x_sendfile'] = True

            res = _send_file(self.path, **send_file_kwargs)
            if 'X-Sendfile' in res.headers:
                res.headers['X-Accel-Redirect'] = x_accel_redirect

                # In case of X-Sendfile/X-Accel-Redirect, the body is empty,
                # yet werkzeug gives the length of the file. This makes
                # NGINX wait for content that'll never arrive.
                res.headers['Content-Length'] = '0'

        res.headers['X-Content-Type-Options'] = 'nosniff'

        if content_security_policy:  # see also Application.set_csp()
            res.headers['Content-Security-Policy'] = content_security_policy

        if self.public:
            if (res.cache_control.max_age or 0) > 0:
                res.cache_control.public = True
        else:
            res.cache_control.pop('public', '')
            res.cache_control.private = True
        if immutable:
            res.cache_control['immutable'] = None  # None sets the directive

        return res
