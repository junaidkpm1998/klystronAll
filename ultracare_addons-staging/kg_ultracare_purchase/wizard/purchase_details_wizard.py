from odoo import api, fields, models, _


class PurchaseRegister(models.TransientModel):
    """Purchase Register wizard."""

    _name = 'purchase.register.report.wizard'
    _description = 'Report Wizard'

    date_from = fields.Date()
    date_to = fields.Date()
    currency_id = fields.Many2one('res.currency', string="Currency",
                                  default=lambda self: self.env.company.currency_id.id)
    company_id = fields.Many2one(comodel_name='res.company', default=lambda self: self.env.user.company_id,
                                 string='Company')
    # purchase_order = fields.Many2many('purchase.order', 'purchase_order_register_rel', string='Purchase Orders')

    def _export(self, report_type):
        return self._print_report(report_type)

    def button_purchase_register(self):
        self.ensure_one()
        report_type = "qweb-pdf"
        return self._export(report_type)

    def _print_report(self, data):
        res = {}
        data = {
            'model': 'purchase.register.report.wizard',
            'form': self.read()[0]
        }
        return self.env.ref('kg_ultracare_purchase.report_purchase_register_report_wizard_pdf').with_context(
            landscape=False).report_action(self, data=data)
