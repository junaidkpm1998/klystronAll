from odoo import fields, models, api


class KGHRLeaveInherit(models.Model):
    _inherit = "hr.leave"

    @api.model_create_multi
    def create(self, vals_list):
        res = super(KGHRLeaveInherit, self).create(vals_list)
        if res['employee_id'].name != res._get_responsible_for_approval().name and res._get_responsible_for_approval().name not in res.get_leave_req_emp():
            template_id = self.env['ir.model.data']._xmlid_lookup('kg_ygg_hr_holidays.request_for_leave_approval')[2]
            if template_id:
                email_template_obj = self.env['mail.template'].browse(template_id)
                email_template_obj.send_mail(res.id, force_send=True)
        return res

    def get_leave_req_emp(self):
        emp_name = []
        for rec in self:
            if rec.employee_ids:
                for emp in rec.employee_ids:
                    emp_name.append(emp.name)
        return ", ".join(emp_name)
