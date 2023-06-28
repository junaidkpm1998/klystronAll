from odoo import models, fields, api, _

class KGAccountPayment(models.Model):
    _inherit = 'account.payment'
    _description = 'Account Payment'

    cheque_date = fields.Date(string='Cheque Date')
    cheque_no = fields.Char(string='Cheque Number')

class KGAccountPaymentRegister(models.TransientModel):
    _inherit = 'account.payment.register'
    _description = 'Account Payment Register'

    cheque_date = fields.Date(string='Cheque Date')
    cheque_no = fields.Char(string='Cheque Number')
    account_payment_id = fields.Many2one('account.payment',string='Account Payment Id')

    def _create_payment_vals_from_wizard(self, batch_result):
        res = super(KGAccountPaymentRegister, self)._create_payment_vals_from_wizard(batch_result)
        payment_vals = {
            'cheque_date':self.cheque_date,
            'cheque_no':self.cheque_no,
        }
        res.update(payment_vals)
        return res

