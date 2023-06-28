# -*- coding: utf-8 -*-
from datetime import date
import re
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    last_name = fields.Char(required=True)
    initials = fields.Char(required=True)
    nick_name = fields.Char(required=True)
    employee_no = fields.Char()
    age = fields.Integer(compute='compute_age')
    experience = fields.Integer(string='Experience', required=True)
    date_of_joining = fields.Date('Date of Joining', required=True)
    year_of_employment = fields.Date('Year of Employment', required=True)
    bank_id = fields.Many2one('res.bank', required=True)
    manpower_reg_no = fields.Char(required=True)
    residency_no = fields.Char(required=True)
    passport_issue = fields.Date(required=True)
    passport_expiry_date = fields.Date(required=True)
    resign_termination_retirement_date = fields.Date(string='Resigned/Terminated/Retirement Dates', required=True)
    contract_expiry_date = fields.Date(required=True)
    insurance_no = fields.Char(required=True)
    insurance_issue_date = fields.Date(required=True)
    insurance_expiry_date = fields.Date(required=True)
    grade_id = fields.Char(required=True)
    designation_id = fields.Many2one('hr.job', required=True)
    local_address = fields.Text(required=True)
    blood_group = fields.Char(required=True)
    vehicle_id = fields.Many2one('fleet.vehicle', required=True)
    travel_ticket_type = fields.Selection([('business', 'Business'), ('economy', 'Economy')], required=True)
    employee_status = fields.Selection(
        [('active', 'Active'), ('new_joiners', 'New Joiner'), ('transferred', 'Transferred'), ('resigned', 'Resigned'),
         ('terminated', 'Terminated'), ('seconded', 'Seconded'), ('expired', 'Expired')], required=True)
    no_of_tickets_per_year = fields.Integer('No of Tickets Per Year', required=True)
    additional_remarks = fields.Text()
    attachment_ids = fields.Many2many('ir.attachment', string='Attachment', required=True)
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)
    frequency = fields.Integer(string='Frequency of Education Allowance', required=True)
    dependents_ids = fields.One2many('hr_employee.dependents', 'dependent_id')

    is_promoted = fields.Boolean('Is Promoted')
    is_transfer = fields.Boolean('Is Transfer')

    @api.depends('birthday')
    def compute_age(self):
        """computing the age from date of birth with current date"""
        today = date.today()
        dob = self.birthday
        if dob:
            self.age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
        else:
            self.age = False

    @api.model
    def create(self, vals):
        """autogenerate unique employee number"""
        if vals.get('employee_no', _('New')) == _('New'):
            vals['employee_no'] = self.env['ir.sequence'].next_by_code(
                'employee.number') or False
            res = super(HrEmployee, self).create(vals)
            return res

    @api.onchange('birthday')
    def onchange_birthday(self):
        """validation error for date of birth which is greater than current date"""
        today = date.today()
        dob = self.birthday
        if dob and dob > today:
            raise ValidationError('The birthday should be choose less than the current date')

    @api.onchange('insurance_expiry_date', 'passport_expiry_date', 'contract_expiry_date')
    def onchange_expiry_date(self):
        """validation error for expiry date which is less than current date"""
        today = date.today()
        insurance_expiry_date = self.insurance_expiry_date
        passport_expiry_date = self.passport_expiry_date
        contract_expiry_date = self.contract_expiry_date
        if insurance_expiry_date and insurance_expiry_date < today:
            raise ValidationError('The insurance expiry date should be choose greater than the current date')
        elif passport_expiry_date and passport_expiry_date < today:
            raise ValidationError('The passport expiry date should be choose greater than the current date')
        elif contract_expiry_date and contract_expiry_date < today:
            raise ValidationError('The contract expiry date expiry date should be choose greater than the current date')

    @api.onchange('work_email')
    def onchange_private_email(self):
        """validation error for email which is in invalid format"""
        pat = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b'
        email = self.work_email
        if email and not re.match(pat, email):
            print("inValid Email")
            raise ValidationError("Email is in invalid format")


class HrEmployeeDependentsLine(models.Model):
    _name = 'hr_employee.dependents'

    dependent_id = fields.Many2one('hr.employee')

    name = fields.Text('Name', required=True)
    relationship = fields.Selection(
        [('father', 'Father'), ('mother', 'Mother'), ('brother', 'Brother'), ('sister', 'Sister'),
         ('others', 'Others')])
    dob = fields.Date('Date of Birth', required=True)
    gender = fields.Selection([('male', 'Male'), ('female', 'Female'), ('others', 'Others')])
    phone = fields.Char(required=True)
    passport_no = fields.Char(required=True)
    occupation = fields.Char(required=True)
    blood_group = fields.Char(required=True)
    passport_issue = fields.Date(required=True)
    passport_expiry_date = fields.Date(required=True)
    visa_issue_date = fields.Date(required=True)
    visa_expiry_date = fields.Date(required=True)
    resident_card_issue_date = fields.Date(required=True)
    resident_card_expiry_date = fields.Date(required=True)
    document_ids = fields.Many2many('ir.attachment', string='Document', required=True)
    nationality = fields.Many2one('res.country', required=True)
    passport_issue_date = fields.Date(required=True)

    insurance_no = fields.Char(required=True)
    insurance_issue_date = fields.Date(required=True)
    insurance_expiry_date = fields.Date(required=True)
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.ref('base.main_company').currency_id)
    education_allowance = fields.Monetary('Allowance', required=True)
    frequency_of_education_allowance = fields.Integer('Frequency of Education Allowance', required=True)

    @api.onchange('dob')
    def onchange_birthday(self):
        """validation error for date of birth which is less than current date"""
        today = date.today()
        dob = self.dob
        if dob and dob > today:
            raise ValidationError('The birthday should be choose less than the current date')

    @api.onchange('passport_expiry_date', 'visa_expiry_date', 'resident_card_expiry_date', 'insurance_expiry_date')
    def onchange_expiry_date(self):
        """validation error for expiry date which is less than current date"""
        today = date.today()
        insurance_expiry_date = self.insurance_expiry_date
        passport_expiry_date = self.passport_expiry_date
        visa_expiry_date = self.visa_expiry_date
        resident_card_expiry_date = self.resident_card_expiry_date

        if insurance_expiry_date and insurance_expiry_date < today:
            raise ValidationError('The insurance expiry date should be choose greater than the current date')
        elif passport_expiry_date and passport_expiry_date < today:
            raise ValidationError('The passport expiry date should be choose greater than the current date')
        elif visa_expiry_date and visa_expiry_date < today:
            raise ValidationError('The visa expiry date  expiry date should be choose greater than the current date')
        elif resident_card_expiry_date and resident_card_expiry_date < today:
            raise ValidationError(
                'The resident card expiry_date  expiry date should be choose greater than the current date')
