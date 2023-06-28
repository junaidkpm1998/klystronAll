
from odoo import _, fields,api, models
from odoo.exceptions import UserError
from ast import literal_eval
import logging
_logger = logging.getLogger(__name__)



class SaleCreditNotification(models.TransientModel):
    _name = 'sale.credit.notification'
    _description = 'Sale Credit Notification'

    msg = fields.Char(readonly=True)

    def close(self):
        return True