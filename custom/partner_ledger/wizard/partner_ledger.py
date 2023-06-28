from odoo import models, fields


class PartnerLedgerWizard(models.TransientModel):
    _name = 'partner.ledger.wizard'

    start_date = fields.Date(string="Start Date")
    end_date = fields.Date(string="End Date")

    def dynamic_report_partner_ledger(self):
        print("dynamic_report_partner_ledger")

    def create_pdf_report_partner_ledger(self):
        print("create_pdf_report_partner_ledger")
        data = {

        }
        return self.env.ref('partner_ledger.action_pdf_report_partner_ledger').report_action(None, data=data)
