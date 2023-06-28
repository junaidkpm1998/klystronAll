from odoo import api, fields, models, _


class SalesWizard(models.TransientModel):
    """Sales Statement wizard."""

    _name = 'sales.report.wizard'
    _description = 'Report Wizard'

    date_from = fields.Date()
    date_to = fields.Date()
    currency_id = fields.Many2one('res.currency', string="Currency",default=lambda self: self.env.company.currency_id.id)
    company_id = fields.Many2one(comodel_name='res.company', default=lambda self: self.env.user.company_id, string='Company')

    def _export(self, report_type):
        return self._print_report(report_type)

    def sale_quotation_print(self):
        self.ensure_one()
        report_type = "qweb-pdf"
        return self._export(report_type)


    def _print_report(self, data):
        res = {}
        data = {
            'model': 'sales.report.wizard',
            'form': self.read()[0]
        }
        return self.env.ref('kg_ultracare_sale.action_sales_report_statement').with_context(landscape=False).report_action(self, data=data)

