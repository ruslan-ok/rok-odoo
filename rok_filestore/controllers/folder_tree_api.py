import mimetypes
import os
from odoo import http
from odoo.http import request

from PIL import Image
from io import BytesIO


class FolderTreeAPI(http.Controller):

    def _get_user_filestore_path(self):
        user = request.env.user
        # You can add a default path or error handling here
        return user.filestore_path

    def build_tree(self, base_path, root_path):
        tree = []
        for entry in sorted(os.listdir(base_path)):
            full_path = os.path.join(base_path, entry)
            if os.path.isdir(full_path):
                has_children = any(
                    os.path.isdir(os.path.join(full_path, child))
                    for child in os.listdir(full_path)
                )
                node = {
                    'name': entry,
                    'path': os.path.relpath(full_path, root_path),
                    'has_children': has_children,
                }
                tree.append(node)
        return tree

    @http.route('/rok_filestore/api/folders', type='json', auth='user')
    def get_folders_tree(self, path=''):
        root_path = self._get_user_filestore_path()
        if not root_path:
            return []
        abs_path = os.path.join(root_path, path)
        # Security: do not allow to leave the user's root directory
        abs_path = os.path.abspath(abs_path)
        if not abs_path.startswith(os.path.abspath(root_path)):
            return []
        return self.build_tree(abs_path, root_path)

    @http.route('/rok_filestore/api/files', type='json', auth='user')
    def get_files(self, path):
        root_path = self._get_user_filestore_path()
        if not root_path:
            return []
        abs_path = os.path.join(root_path, path)
        abs_path = os.path.abspath(abs_path)
        if not abs_path.startswith(os.path.abspath(root_path)) or not os.path.isdir(abs_path):
            return []
        result = []
        for fname in sorted(os.listdir(abs_path)):
            fpath = os.path.join(abs_path, fname)
            if os.path.isfile(fpath):
                mimetype, _ = mimetypes.guess_type(fpath)
                result.append({
                    'name': fname,
                    'path': os.path.join(path, fname),
                    'mimetype': mimetype or 'application/octet-stream',
                    'is_image': (mimetype or '').startswith('image/')
                })
        return result

    @http.route('/rok_filestore/file', type='http', auth='user')
    def serve_file(self, path, **kwargs):
        root_path = self._get_user_filestore_path()
        if not root_path:
            return request.not_found()
        full_path = os.path.join(root_path, path.lstrip("/"))
        full_path = os.path.abspath(full_path)
        if not full_path.startswith(os.path.abspath(root_path)) or not os.path.isfile(full_path):
            return request.not_found()
        mimetype, _ = mimetypes.guess_type(full_path)
        with open(full_path, 'rb') as f:
            content = f.read()
        return http.Response(content, content_type=mimetype or 'application/octet-stream', headers={
            'Content-Disposition': f'inline; filename="{os.path.basename(full_path)}"'
        })

    @http.route('/rok_filestore/thumbnail', type='http', auth='user')
    def serve_thumbnail(self, path, size=128, **kwargs):
        root_path = self._get_user_filestore_path()
        if not root_path:
            return request.not_found()
        full_path = os.path.join(root_path, path.lstrip("/"))
        full_path = os.path.abspath(full_path)
        if not full_path.startswith(os.path.abspath(root_path)) or not os.path.isfile(full_path):
            return request.not_found()
        try:
            size = int(size)
            with Image.open(full_path) as img:
                img.thumbnail((size, size))
                if img.mode in ("RGBA", "LA"):
                    background = Image.new("RGB", img.size, (255, 255, 255))
                    background.paste(img, mask=img.split()[-1])
                    img = background
                elif img.mode != "RGB":
                    img = img.convert("RGB")
                buf = BytesIO()
                img.save(buf, format="JPEG")
                buf.seek(0)
                return http.Response(
                    buf.read(),
                    content_type="image/jpeg",
                    headers={
                        'Content-Disposition': f'inline; filename="thumb_{os.path.basename(full_path)}"'
                    }
                )
        except Exception:
            return request.not_found()
