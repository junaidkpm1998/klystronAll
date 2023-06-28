import datetime

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class StatementReportWizard(models.TransientModel):
    """Statement Report wizard."""

    _name = 'kg.salesman.statement.wizard'
    _description = 'Report Wizard'

    date_from = fields.Date()
    date_to = fields.Date(string='As On',default=datetime.date.today())
    currency_id = fields.Many2one('res.currency', string="Currency",
                                  default=lambda self: self.env.company.currency_id.id)
    company_id = fields.Many2one(comodel_name='res.company', default=lambda self: self.env.user.company_id,
                                 string='Company')
    account_type = fields.Selection(
        [("asset_receivable", "Receivable"), ("liability_payable", "Payable")],
        default="asset_receivable", string='Account Type')

    def _export(self, report_type):
        return self._print_report(report_type)

    def button_statement_report(self):
        self.ensure_one()
        report_type = "qweb-pdf"
        return self._export(report_type)

    def _print_report(self, data):
        res = {}
        data = {
            'model': 'kg.salesman.statement.wizard',
            'form': self.read()[0]
        }
        return self.env.ref('kg_ultracare_salesmanwise_report.action_statement_report').with_context(
            landscape=False).report_action(self, data=data)
