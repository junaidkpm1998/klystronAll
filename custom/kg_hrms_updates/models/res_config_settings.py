from ast import literal_eval

from odoo import models, fields, api


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    salary_head_ids = fields.Many2many('res.users', 'emp_salary_head_rel', string="Salary Heads")

    def set_values(self):
        """Set Value"""
        res = super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param('kg_hrms_updates.salary_head_ids', self.salary_head_ids.ids)
        return res

    @api.model
    def get_values(self):
        """get Value"""

        res = super(ResConfigSettings, self).get_values()

        with_user = self.env['ir.config_parameter'].sudo()
        emp_salary_heads = with_user.get_param('kg_hrms_updates.salary_head_ids')
        res.update(
            salary_head_ids=[(6, 0, literal_eval(emp_salary_heads))] if emp_salary_heads else False, )
        return res
