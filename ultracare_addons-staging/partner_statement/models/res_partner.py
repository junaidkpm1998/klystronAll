from odoo import models


class KGResPartner(models.Model):
    _inherit = "res.partner"

    def _get_pdc_vals(self):
        pdc_vals = []
        pdc_id = self.env['pdc.wizard'].search([('partner_id', '=', self.id), ('state', '=', 'done')])
        for vals in pdc_id:
            pdc_number = vals.name
            invoice_reference = vals.memo
            payment_date = vals.payment_date
            due_date = vals.due_date
            payment_amount = vals.payment_amount
            pdc = {
                'pdc_number': pdc_number,
                'invoice_reference': invoice_reference,
                'type': dict(vals.fields_get(allfields=['type'])['type']['selection'])[vals.type],
                'payment_type': dict(vals.fields_get(allfields=['payment_type'])['payment_type']['selection'])[
                    vals.payment_type],
                'payment_date': payment_date,
                'due_date': due_date,
                'payment_amount': payment_amount,
                'partner_id': vals.partner_id.name
            }
            if pdc:
                pdc_vals.append(pdc)

        return pdc_vals
