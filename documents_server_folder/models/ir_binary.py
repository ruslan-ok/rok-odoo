from odoo import models
from .dsf_stream import DsfStream

class IrBinary(models.AbstractModel):
    _inherit = 'ir.binary'

    # Rok todo: check
    def _record_to_stream(self, record, field_name):
        if record._name == 'documents.document' and field_name == 'raw' and record.located_on_the_server:
            return DsfStream.from_path(record.get_full_path())
        return super()._record_to_stream(record, field_name)
