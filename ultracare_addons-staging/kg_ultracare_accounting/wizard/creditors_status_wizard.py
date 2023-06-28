from datetime import date

from odoo import api, fields, models, _


class CreditorsStatusWizard(models.TransientModel):
    """Creditors Status wizard."""

    _name = 'creditors.status.report.wizard'
    _description = 'Report Wizard'

    date_end = fields.Date(required=True,default=fields.Date.to_string(date.today()),string='As on',readonly=1)
    currency_id = fields.Many2one('res.currency', string="Currency",
                                  default=lambda self: self.env.company.currency_id.id)
    company_id = fields.Many2one(comodel_name='res.company', default=lambda self: self.env.user.company_id,
                                 string='Company')


    def _export(self, report_type):
        return self._print_report(report_type)


    def button_creditors_status_report(self):
            self.ensure_one()
            report_type = "qweb-pdf"
            return self._export(report_type)


    def _print_report(self, data):
        res = {}
        data = {
            'model': 'creditors.status.report.wizard',
            'form': self.read()[0]
        }
        return self.env.ref('kg_ultracare_accounting.action_creditors_status_report').with_context(
            landscape=False).report_action(self, data=data)
