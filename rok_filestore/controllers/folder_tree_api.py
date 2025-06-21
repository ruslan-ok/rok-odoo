import mimetypes
import os
from odoo import http
from odoo.http import request

FILE_STORAGE_PATH = "/mnt/c/Users/ruslan/Documents/Projects/rok/rok-apps_data/rok/docs/ruslan"

class FolderTreeAPI(http.Controller):

    def build_tree(self, base_path, depth=0):
        tree = []
        for entry in sorted(os.listdir(base_path)):
            full_path = os.path.join(base_path, entry)
            if os.path.isdir(full_path):
                node = {
                    'name': entry,
                    'path': os.path.relpath(full_path, FILE_STORAGE_PATH),
                    'children': self.build_tree(full_path, depth + 1) if depth < 1 else [],
                }
                tree.append(node)
        return tree

    @http.route('/rok_filestore/api/folders', type='json', auth='user')
    def get_folders_tree(self):
        return self.build_tree(FILE_STORAGE_PATH)

    @http.route('/rok_filestore/api/files', type='json', auth='user')
    def get_files(self, path):
        abs_path = os.path.join(FILE_STORAGE_PATH, path)
        if not os.path.isdir(abs_path):
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
        full_path = os.path.join(FILE_STORAGE_PATH, path)
        if not os.path.isfile(full_path):
            return request.not_found()
        mimetype, _ = mimetypes.guess_type(full_path)
        with open(full_path, 'rb') as f:
            content = f.read()
        return http.Response(content, content_type=mimetype or 'application/octet-stream', headers={
            'Content-Disposition': f'inline; filename="{os.path.basename(full_path)}"'
        })
