from odoo import fields, models, _, api


class HREmployeeRequest(models.Model):
    _name = 'hr.employee.requests'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Request Reference', required=True, copy=False,
                       default=lambda self: _('New'))
    employee_id = fields.Many2one('hr.employee', string='Employee')
    request_date = fields.Date(string='Date')
    document_type = fields.Selection([('no objection certificate', 'No Objection Certificate'),
                                      ('experience certificate', 'Experience Certificate'),
                                      ('salary balance certificate', 'Salary Balance Certificate'),
                                      ('employment certificate', 'Employment Certificate')])
    state = fields.Selection([('draft', 'Draft'), ('confirm', 'Confirm')], default='draft')

    @api.model
    def create(self, vals):
        """autogenerate unique document number"""
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'hr.employee.requests') or _('New')
        res = super(HREmployeeRequest, self).create(vals)
        return res

    def action_confirm(self):
        """confirmed button"""
        self.state = 'confirm'
