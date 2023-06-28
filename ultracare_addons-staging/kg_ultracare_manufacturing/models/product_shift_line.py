from datetime import datetime
import logging
from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class ProductionShiftLine(models.Model):
    _name = 'product.shift.line'
    _description = 'Product Shift Line'
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _rec_name = 'kg_product'

    state = fields.Selection(
        [('new', 'New'), ('prod_com', 'Production Completed'), ('transfer', 'Transfered to Stock')], 'State',
        default='new')

    @api.depends('kg_qty', 'kg_act_prod')
    def _compute_balance(self):
        for file in self:
            file.kg_balance = file.kg_qty - file.kg_done_qty
            if file.kg_balance == 0:
                file.kg_act_prod = 0

    @api.depends('kg_qty', 'kg_act_prod')
    def _compute_done(self):
        for file in self:
            mrps = self.env['mrp.production'].search([
                ('production_planning_id', '=', file.kg_prod_plan_id.id),
                ('state', '=', 'done'), ('product_id', '=', file.kg_product.id)])
            qty = 0
            if mrps:
                qty = sum(mrp.qty_produced for mrp in mrps)
            file.kg_done_qty = qty

    kg_balance = fields.Float(string="Balance", compute='_compute_balance')
    kg_done_qty = fields.Float(string="Done Qty", compute='_compute_done')
    kg_prod_tot_balance = fields.Float(string="Total Balance")  # , compute='_compute_prod_balance')
    kg_total_act_prod = fields.Float(string="Actual Produced")  # , compute='_compute_tot_produce')
    kg_waste_per = fields.Float(string="Wastage %", compute='_calculate_waste_percentage')
    raw_material_ids = fields.Many2many('production.dummy.line', 'raw_line_rel', string="Raw Material")

    def _calculate_waste_percentage(self):
        for i in self:
            if (i.kg_product.weight_uom and i.kg_act_prod) > 0.00:
                waste_per = i.kg_wastage_calculation * 100 / (i.kg_product.weight_uom * .001 * i.kg_act_prod)
                i.kg_waste_per = waste_per
            else:
                i.kg_waste_per = 0

    @api.onchange('kg_shift_id')
    def _onchange_kg_shift_id(self):
        for file in self:
            if file.kg_shift_id:
                if file.kg_shift_id.start_am_pm == 'pm':
                    start_time = file.kg_shift_id.start_time
                else:
                    start_time = file.kg_shift_id.start_time
                if file.kg_shift_id.end_am_pm == 'pm':
                    end_time = file.kg_shift_id.end_time
                else:
                    end_time = file.kg_shift_id.end_time
                file.kg_start_time = start_time
                file.kg_end_time = end_time

    def send_to_stock(self):
        for record in self:
            vals = {}
            vals['picking_type_id'] = self.env['stock.picking.type'].search(
                [('name', '=', 'Internal Transfers to Stock from production')], limit=1).id
            vals['location_id'] = self.env['stock.location'].search(
                [('name', '=', 'Production'), ('usage', '=', 'internal')],
                limit=1).id
            vals['location_dest_id'] = self.env['stock.location'].search(
                [('name', '=', 'Stock'), ('usage', '=', 'internal')],
                limit=1).id
            picking_type = self.env['stock.picking.type'].search([('code', '=', 'internal')], limit=1)
            vals['picking_type_id'] = picking_type[0].id
            pick_id = self.env['stock.picking'].create(vals)
            vals_line = {}
            vals_line['product_id'] = record.kg_product.id
            vals_line['name'] = record.kg_product.name
            vals_line['product_uom'] = record.kg_product.uom_id.id
            vals_line['product_uom_qty'] = record.kg_act_prod
            vals_line['location_id'] = self.env['stock.location'].search(
                [('name', '=', 'Production'), ('usage', '=', 'internal')],
                limit=1).id
            vals_line['location_dest_id'] = self.env['stock.location'].search(
                [('name', '=', 'Stock'), ('usage', '=', 'internal')],
                limit=1).id
            vals_line['picking_id'] = pick_id.id
            move = self.env['stock.move'].create(vals_line)
            pick_id.action_confirm()
            pick_id.button_validate()

            record.write({'picking_id': pick_id.id, 'state': 'transfer'})

    def complete_prod(self):
        for record in self:
            if record.kg_act_prod > 0:
                bom_id = self.env['mrp.bom'].search([('product_tmpl_id', '=', record.kg_product.product_tmpl_id.id)],
                                                    limit=1)
                # Log
                _logger.info("bom_id %s" % bom_id)
                if not bom_id:
                    raise UserError('Create BOM for Product.')

                # Get Masters
                location_production = self.env['stock.location'].search(
                    [('name', '=', 'Production'), ('usage', '=', 'internal')])
                location_stock = self.env['stock.location'].search(
                    [('name', '=', 'Stock'), ('usage', '=', 'internal')])
                operation = self.env['stock.picking.type'].search([('code', '=', 'mrp_operation')])

                # Log
                _logger.info("location_production %s" % location_production)
                _logger.info("operation %s" % operation)

                # Create MRP
                vals = {}
                vals['product_id'] = record.kg_product.id
                vals['product_qty'] = record.kg_act_prod
                vals['bom_id'] = bom_id.id
                vals['production_planning_id'] = record.kg_prod_plan_id.id
                vals['date_planned_start'] = record.kg_date
                vals['kg_shift_id'] = record.kg_shift_id.id
                vals['kg_day'] = record.kg_day
                vals['picking_type_id'] = operation[0].id
                vals['location_src_id'] = location_production[0].id
                vals['location_dest_id'] = location_stock[0].id
                vals['company_id'] = self.env.company.id
                vals['consumption'] = 'flexible'
                prod_id = self.env['mrp.production'].create(vals)

                move_raw_ids = prod_id.move_raw_ids
                print(move_raw_ids.bom_line_id)
                # prod_id._onchange_product_id()
                for raw in move_raw_ids:
                    print(raw.bom_line_id,"LINEEE")
                    if not raw.product_id.is_dummy_prod:
                        if raw.state != 'assigned' and raw.product_id.detailed_type == 'product':
                            quants = self.env['stock.quant'].search(
                                [('product_id', '=', raw.product_id.id), ('location_id', '=', raw.location_id.id)])
                            qty_qnt = 0
                            for file in quants:
                                if file.quantity:
                                    qty_qnt += file.quantity
                            if qty_qnt == 0:
                                raise UserError(_(
                                    'Raw material not available in production location: "%s".\n Stock Available : %s\n '
                                    'Stock Required : %s') % (
                                                    raw.product_id.name, qty_qnt, raw.product_uom_qty))
                    if raw.product_id.is_dummy_prod:
                        actual = record.kg_prod_plan_id.get_actual_prod(raw.product_id)
                        raw.write({
                            'product_id': actual.id,
                            'product_uom': actual.uom_id.id,
                            'bom_line_id': False
                        })
                # prod_id.action_confirm()
                prod_id.update({'qty_producing': record.kg_act_prod,
                                'product_uom_qty': record.kg_act_prod,
                                'product_qty': record.kg_act_prod,
                                })
                prod_id._onchange_producing()
            return True

    # Field Declaration
    name = fields.Char('Name')
    kg_product = fields.Many2one('product.product', 'Product')
    kg_machine = fields.Many2one(related='kg_product.kg_machine', string='Machine')
    ready_mo = fields.Boolean(string='Ready MO', default=False, compute='_compute_ready_mo')
    kg_day = fields.Char('Day')
    kg_date = fields.Date('Date')
    kg_shift_id = fields.Many2one('shift.master', string="Shift")
    kg_qty = fields.Float('Target')
    kg_forecast = fields.Float('Forecast', compute='comp_real_mins1', store=True)
    kg_planned = fields.Float('Production')
    kg_act_prod = fields.Float('Actual Produced')
    kg_trrt = fields.Float('TRRT(hours)')
    kg_sch_min = fields.Float('Scheduled Mins')
    kg_in_stock = fields.Float('In Stock')
    kg_can_produce = fields.Float('Can Produce')
    kg_start_time = fields.Float('Start Time')
    kg_end_time = fields.Float('End Time')
    kg_real_mins = fields.Float('Scheduled Mins', compute='comp_real_mins1')
    kg_act_mins = fields.Float('Actual Mins', compute='comp_real_mins1')
    kg_dt = fields.Float('DT(mins)')
    kg_eff = fields.Float('Efficency(%)', compute='comp_real_mins1', group_operator='avg')
    kg_over_shift = fields.Boolean('Over Shift Hours', compute='comp_over_shift')
    kg_forecast_act_per = fields.Float('MTD Production Target(%)', compute='comp_real_mins1')
    kg_wastage_calculation = fields.Float('Wastage (KG)')

    @api.depends('kg_act_prod')
    def _compute_ready_mo(self):
        for rec in self:
            if rec.kg_act_prod:
                rec.ready_mo = True
            else:
                rec.ready_mo = False

    @api.depends('kg_trrt')
    def comp_over_shift(self):
        for record in self:
            act_conf = self.env['kg.prod.conf'].search([('active', '=', True)])
            if not act_conf:
                raise UserError(_('Create Active Production Configuration'))
            shift_hrs = act_conf.kg_shift_hours
            dt = record.kg_date
            shift = record.kg_shift_id and record.kg_shift_id.id or False
            mach = record.kg_machine and record.kg_machine.id or False
            if dt and shift and mach:
                lines = self.search([('kg_prod_plan_id', '=', record.kg_prod_plan_id.id), ('kg_machine', '=', mach),
                                     ('kg_date', '=', dt), ('kg_shift_id', '=', shift)])
                real_hr = 0
                if lines:
                    for line in lines:
                        real_hr += line.kg_trrt
                if real_hr > shift_hrs:
                    record.kg_over_shift = True
                else:
                    record.kg_over_shift = False
            else:
                record.kg_over_shift = False

    kg_remarks = fields.Char('Remarks')
    kg_prod_plan_id = fields.Many2one('production.planning', 'Production Plan')
    # kg_prod_planning_id = fields.Many2one('production.planning', 'Production Plan')
    production_id = fields.Many2one('mrp.production', 'MRP Ref')
    picking_id = fields.Many2one('stock.picking', 'Picking')

    _sql_constraints = [('uniq_lines', 'unique(kg_product,kg_prod_plan_id,kg_date,kg_shift_id)',
                         _("Already Planned For that Product in same shift and day!"))]

    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        """
            Inherit read_group to calculate the sum of the non-stored fields, as it is not automatically done anymore through the XML.
        """
        if 'kg_start_time' in fields:
            fields.remove('kg_start_time')
        if 'kg_end_time' in fields:
            fields.remove('kg_end_time')
        res = super(ProductionShiftLine, self).read_group(domain, fields, groupby, offset=offset, limit=limit,
                                                          orderby=orderby, lazy=lazy)
        fields_list = ['kg_real_mins', 'kg_act_mins', 'kg_eff', 'kg_forecast', 'kg_forecast_act_per']
        if any(x in fields for x in fields_list):
            # Calculate first for every product in which line it needs to be applied
            re_ind = 0
            prod_re = {}
            tot_products = self.browse([])
            for re in res:
                if re.get('__domain'):
                    products = self.search(re['__domain'])
                    tot_products |= products
                    for prod in products:
                        prod_re[prod.id] = re_ind
                re_ind += 1
            res_val = tot_products.comp_real_mins1(field_names=[x for x in fields if fields in fields_list])
            for key in res_val.keys():
                count = 0
                for l in res_val[key].keys():
                    re = res[prod_re[key]]
                    count += 1
                    if re.get(l):
                        # if l !='kg_forecast':
                        re[l] += res_val[key][l]
                    else:
                        re[l] = res_val[key][l]
                # if 'kg_product_count' in re:
                #     re['kg_forecast']=re['kg_forecast']/re['kg_product_count']
                if 'kg_qty' in re and re['kg_qty'] > 0:
                    re['kg_eff'] = (re['kg_act_prod'] / re['kg_qty']) * 100.0

                if 'kg_forecast' in re and re['kg_forecast'] > 0:
                    re['kg_forecast_act_per'] = (re['kg_act_prod'] / re['kg_forecast']) * 100.0
        return res

    @api.onchange('kg_product')
    def onchange_product(self):
        for record in self:
            qty = 0
            sf_lines = self.env['kg.sf.lines'].search(
                [('kg_product_id', '=', record.kg_product.id), ('kg_sf_id', '=', record.kg_prod_plan_id.kg_sf_id.id)])
            if sf_lines:
                for line in sf_lines:
                    qty += line.kg_net
            record.kg_in_stock = record.kg_product.with_context({'location': 8}).qty_available
            record.kg_forecast = qty

    def comp_real_mins1(self, field_names=None):
        res = {}
        if field_names is None:
            field_names = []

        for val in self:
            res[val.id] = {}
            if val.kg_start_time < val.kg_end_time:
                value = val.kg_end_time - val.kg_start_time
                res[val.id]['kg_real_mins'] = value * 60
                res[val.id]['kg_act_mins'] = (value * 60) - val.kg_dt

            else:
                value = (24 - val.kg_start_time) + val.kg_end_time
                res[val.id]['kg_real_mins'] = value * 60
                res[val.id]['kg_act_mins'] = (value * 60) - val.kg_dt
                # res[val.id]['kg_real_mins'] = 0.0
                # res[val.id]['kg_act_mins'] = 0.0

            if val.kg_qty > 0:
                act = val.kg_act_prod
                tar = val.kg_qty
                eff = (act / tar) * 100
                res[val.id]['kg_eff'] = eff
            else:
                res[val.id]['kg_eff'] = 0

            if val.kg_product:
                qty = 0
                sf_lines = self.env['kg.sf.lines'].search(
                    [('kg_product_id', '=', val.kg_product.id), ('kg_sf_id', '=', val.kg_prod_plan_id.kg_sf_id.id)])
                if sf_lines:
                    for line in sf_lines:
                        qty += line.kg_net
                res[val.id]['kg_forecast'] = qty

                if qty > 0:
                    res[val.id]['kg_forecast_act_per'] = ((val.kg_act_prod) / qty) * 100.0
                else:
                    res[val.id]['kg_forecast_act_per'] = 0

            for k, v in res[val.id].items():
                setattr(val, k, v)
        return res

    # @api.depends('kg_qty', 'kg_product')
    # def compute_trrt(self):
    #     for record in self:
    #         if record.kg_product:
    #             cph = float(record.kg_product.eff_output_carton)
    #             if cph > 0:
    #                 dt = float(record.kg_product.sch_shift_hours)
    #                 target = record.kg_qty
    #                 trrt = (target / cph) + dt
    #             else:
    #                 trrt = 0
    #             record.kg_trrt = round(trrt, 1)

    # @api.depends('kg_qty', 'kg_product')
    # def comp_production(self):
    #     if self.kg_product:
    #         lines = self.search(
    #             [('kg_prod_plan_id', '=', self.kg_prod_plan_id.id), ('kg_product', '=', self.kg_product.id)])
    #         qty = 0
    #         if lines:
    #             for line in lines:
    #                 qty += line.kg_qty
    #         self.kg_planned = qty

    @api.onchange('kg_date')
    def onchange_date(self):
        for i in self:
            date = i.kg_date
            if not date:
                return {}
            date = str(i.kg_date) + " " + "00:00:00"
            date_time = datetime.strptime(date, '%Y-%m-%d %H:%M:%S')
            weekday = int(date_time.weekday())
            dict_day = {0: "Monday", 1: "Tuesday", 2: "Wednesday", 3: "Thursday", 4: "Friday", 5: "Saturday",
                        6: "Sunday"}
            if weekday >= 0:
                i.kg_day = dict_day[weekday]

    def create_mrp(self):
        product_tmpl_id = self.kg_prod_plan_id.kg_product.product_tmpl_id.id
        uom_id = self.kg_prod_plan_id.uom_id.id
        bom_id = self.env['mrp.bom'].search(
            [('product_tmpl_id', '=', product_tmpl_id), ('product_uom_id', '=', uom_id)])
        bom_main_qty = bom_id.product_qty
        if len(bom_id) == 0:
            raise UserError(
                _('no BOM found for this product and defined UOM,please define BOM First with product and uom'))
        if len(bom_id) > 1:
            raise UserError(_('multiple bom found for same product'))
        bom_line = bom_id.bom_line_ids
        bom_line_length = len(bom_line)
        if bom_line_length == 0:
            raise UserError(_('inside BOM no lines found'))
        shift_id = self.kg_shift_id and self.kg_shift_id.id
        for bl in bom_line:
            product_id = bl.product_id and bl.product_id.id
            product_uom_id = bl.product_uom_id and bl.product_uom_id.id
            product_qty = float(bl.product_qty / bom_main_qty) * float(self.kg_qty)
            self.env['kg.raw.mat.line'].create({'kg_product': product_id, 'kg_product_uom': product_uom_id,
                                                'kg_date': self.kg_date, 'kg_shift_id': shift_id, 'kg_qty': product_qty,
                                                'kg_prod_plan_id': self.kg_prod_plan_id.id})

        vals_mrp = {}
        vals_mrp['kg_shift_id'] = shift_id
        vals_mrp['kg_day'] = self.kg_day
        vals_mrp['product_id'] = self.kg_prod_plan_id.kg_product.id
        vals_mrp['product_uom_id'] = self.kg_prod_plan_id.kg_product.uom_id.id
        vals_mrp['product_qty'] = self.kg_qty
        vals_mrp['bom_id'] = bom_id.id
        vals_mrp['date_planned_start'] = self.kg_date
        prod = self.env['mrp.production'].create(vals_mrp)
        self.production_id = prod.id
        lines = self.kg_prod_plan_id.kg_shift_lines
        lines_length = len(lines)
        production_ids = []
        for li in lines:
            if li.production_id and li.production_id.id:
                production_ids.append(li.production_id.id)
        production_ids_len = len(production_ids)
        if production_ids_len == lines_length:
            self.state = 'done'
        else:
            self.state = 'progress'
        return True
