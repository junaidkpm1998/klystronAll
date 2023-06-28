import base64

from odoo import api, fields, models, Command,_
from odoo.tools.misc import formatLang, format_date, get_lang



class KGFollowupManualReminder(models.TransientModel):
    _inherit = 'account_followup.manual_reminder'

    def default_get(self, fields_list):
        defaults = super().default_get(fields_list)
        report = self.env['ir.actions.report']._render_qweb_pdf('partner_statement.action_print_outstanding_statement',
                                                                defaults['partner_id'])
        att_id = self.env['ir.attachment'].create({
            'name': 'Outstanding Statement',
            'type': 'binary',
            'datas': base64.b64encode(report[0]),
            'res_model': 'res.partner',
            'res_id': defaults['partner_id'],
            'mimetype': 'application/x-pdf'
        })
        assert self.env.context['active_model'] == 'res.partner'
        partner = self.env['res.partner'].browse(self.env.context['active_ids'])
        partner.ensure_one()
        followup_line = partner.followup_line_id
        if followup_line:
            defaults.update(
                email=followup_line.send_email,
                sms=followup_line.send_sms,
                template_id=followup_line.mail_template_id.id,
                sms_template_id=followup_line.sms_template_id.id,
                join_invoices=followup_line.join_invoices,
            )
        defaults.update(
            partner_id=partner.id,
            email_recipient_ids=[Command.set((partner._get_all_followup_contacts() or partner).ids)],
            attachment_ids=[Command.set(att_id.ids)],
        )
        return defaults


class KGresPartnerInherit(models.Model):
    _inherit = "res.partner"

    def execute_followup(self, options):
        """ Execute the actions to do with follow-ups for this partner.
        This is called when processing the follow-ups manually, via the wizard.

        options is a dictionary containing at least the following information:
            - 'partner_id': id of partner (self)
            - 'email': boolean to trigger the sending of email or not
            - 'email_subject': subject of email
            - 'followup_contacts': partners (contacts) to send the followup to
            - 'body': email body
            - 'attachment_ids': invoice attachments to join to email/letter
            - 'sms': boolean to trigger the sending of sms or not
            - 'sms_body': sms body
            - 'print': boolean to trigger the printing of pdf letter or not
            - 'manual_followup': boolean to indicate whether this followup is triggered via the manual reminder wizard
        """
        self.ensure_one()
        partner = self.env['res.partner'].browse(self.env.context['active_ids'])
        to_print = self._execute_followup_partner(options=options)
        if options.get('print') and to_print:
            report = self.env['ir.actions.report']._render_qweb_pdf(
                'partner_statement.action_print_outstanding_statement', partner.id)
            return self.env['account.followup.report']._print_followup_letter(self, options)


class KGAccountFollowupReport(models.AbstractModel):
    _inherit = 'account.followup.report'

    @api.model
    def _print_followup_letter(self, partner, options=None):
        """Generate the followup letter for the given partner.
        The letter is saved as ir.attachment and linked in the chatter.

        Returns a client action downloading this letter and closing the wizard.
        """
        action = self.env.ref('partner_statement.action_print_outstanding_statement')
        tz_date_str = format_date(self.env, fields.Date.today(),
                                  lang_code=self.env.user.lang or get_lang(self.env).code)
        followup_letter_name = _("Follow-up %s - %s", partner.display_name, tz_date_str)
        followup_letter = action._render_qweb_pdf('partner_statement.outstanding_statement', partner.id,
                                                  data={'options': options or {}})[0]
        attachment = self.env['ir.attachment'].create({
            'name': followup_letter_name,
            'raw': followup_letter,
            'res_id': partner.id,
            'res_model': 'res.partner',
            'type': 'binary',
            'mimetype': 'application/pdf',
        })
        partner.message_post(body=_('Follow-up letter generated'), attachment_ids=[attachment.id])
        return {
            'type': 'ir.actions.client',
            'tag': 'close_followup_wizard',
            'params': {
                'url': '/web/content/%s?download=1' % attachment.id,
            }
        }
