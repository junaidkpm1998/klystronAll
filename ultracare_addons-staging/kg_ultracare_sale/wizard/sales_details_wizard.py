from odoo import api, fields, models, _
from dateutil.relativedelta import relativedelta

from odoo.exceptions import ValidationError


class SaleAnalysisWizard(models.TransientModel):
    """Sales Details wizard."""

    _name = 'sales.details.report.wizard'
    _description = 'Report Wizard'

    date_from = fields.Date()
    date_to = fields.Date()
    currency_id = fields.Many2one('res.currency', string="Currency",
                                  default=lambda self: self.env.company.currency_id.id)
    company_id = fields.Many2one(comodel_name='res.company', default=lambda self: self.env.user.company_id,
                                 string='Company')
    last_first_year_start = fields.Date('Last First Year Start')
    last_first_year_end = fields.Date('Last First Year End')
    last_second_year_start = fields.Date('Last Second Year Start')
    last_second_year_end = fields.Date('Last Second Year End')

    @api.onchange('date_from','date_to')
    def _onchange_last_years(self):
        for rec in self:
            if rec.date_from:
                rec.last_first_year_start = rec.date_from - relativedelta(years=1)
                rec.last_second_year_start = rec.date_from - relativedelta(years=2)
            if rec.date_to:
                rec.last_first_year_end = rec.date_to - relativedelta(years=1)
                rec.last_second_year_end = rec.date_to - relativedelta(years=2)


    def _export(self, report_type):
        return self._print_report(report_type)


    def button_sale_details_report(self):
        if self.date_from > self.date_to:
            raise ValidationError(_('Start Date must be less than End Date'))
        else:
            self.ensure_one()
            report_type = "qweb-pdf"
            return self._export(report_type)


    def _print_report(self, data):
        res = {}
        data = {
            'model': 'sales.details.report.wizard',
            'form': self.read()[0]
        }
        return self.env.ref('kg_ultracare_sale.action_sales_details_report').with_context(
            landscape=False).report_action(self, data=data)
