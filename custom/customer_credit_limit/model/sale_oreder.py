from AptUrl.Helpers import _

from odoo import models, fields, api
from odoo.exceptions import ValidationError


class CustomerCreditLimit(models.Model):
    _inherit = 'sale.order'

    @api.onchange('partner_id')
    def onchange_partner_id_credit(self):
        if self.partner_id:
            if self.partner_id.total_due >= self.partner_id.warning_amount and self.partner_id.total_due <= self.partner_id.blocking_stage:
                print(self.partner_id,"partnr")
                self.write({
                    'partner_id': self.partner_id,
                })
                return {
                    'warning': {
                        'title': _("Warning"),
                        'message': _(
                            "Your Due amounnt is grater than or equal to warning amount'."
                        )
                    }
                }
            elif self.partner_id.total_due >= self.partner_id.blocking_stage:
                print(self.partner_id.name)
                raise ValidationError(('WARNING : Due amounnt is grater than or equal to blocking amount'))


