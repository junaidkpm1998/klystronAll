from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    # alt_desc = fields.Char(string="Alternative Description")


    ply = fields.Float(string="PLY")
    thickness = fields.Float(string="Thickness")
    reel_width = fields.Float(string="Reel Width")
    division_code = fields.Char(string="Division Code")
    sup_part_no = fields.Char(string="Supplier Part No")
    gsm = fields.Float(string="GSM")
    sheet_size = fields.Float(string="Sheet Size")
    sheet_length = fields.Float(string="Sheet Length")
    origin_country = fields.Many2one('res.country', string="Country of Origin")
    stationary_consumed_qty = fields.Float(string="Consumed Qty", Store=True)
    kg_internal_type = fields.Selection([
        ('finish', 'Finished Product'),
        ('spare', 'Spare Parts'),
        ('raw', 'Raw Material'),
        ('service', 'Service'),
        ('misc', 'Miscellaneous')
    ], required=True, string='State', default='misc')
    brand_id = fields.Many2one('product.brand', string="Brand")
    kg_group_id = fields.Many2one('product.group', string="Group")
    sub_group_id = fields.Many2one('product.sub.group', "Sub Group")



    """###*** Finished Products ***"""

    kg_reordering_value = fields.Float(string="Re.Ordering Quantity")
    raw_material_ids = fields.One2many('kg.raw.material', 'material_tmpl_id', string="Raw Material")
    kg_cus_code = fields.Char(string='Customer Code')
    inner_outer_pack_conf = fields.Char(string='Inner * outer Packing Configuration')
    outer_pack_uom = fields.Char(string='Outer Pack / UoM')
    kg_lbl = fields.Char(string="Label Application")
    kg_emb = fields.Char(string="Embossing")
    kg_ply = fields.Char(string='Plies')
    weight_uom = fields.Float(string='Weight per UoM(Grams)')
    kg_width = fields.Char(string='Width(mm)')
    rm_width = fields.Float(string='RM Width(mm)')
    product_length = fields.Float(string='Product Length')
    kg_length = fields.Char(string='Length(mm)')
    tissue_per_pack = fields.Float(string='Tissue Per Pack')
    tissue_per_uom = fields.Float(string='Tissue Per UoM')
    tn_cut_length = fields.Float(string='Cut Length(mm)')
    sch_shift_hours = fields.Char(string='Scheduled DT/Shift Hours')

    kg_sku_type = fields.Char(string='Product Type')
    tr_bale_qty = fields.Float(string='Bale Quantity')
    outer_packing_conf = fields.Char(string='Outer Packing Configuration')
    core_size_ply = fields.Char(string='Core Size(mm)/Core Ply/Perforation')
    kg_hndl = fields.Char(string='Handle Application')
    kg_lam = fields.Char(string='Lamination')
    weight_roll = fields.Float(string='Weight Per Roll(Grams')
    price_per_pirce = fields.Float(string='Price Per Piece')
    defined_weight = fields.Float(string='Weight Per Tissue(Grams)')
    tr_weight_roll = fields.Float(string='Weight Per Rolls(Grams)')
    kg_perf = fields.Char(string='Perforation Length(mm)')
    kg_gsm = fields.Char(string='GSM')
    kg_dia = fields.Char(string='Diameter(mm)')
    tn_sheets_pack = fields.Integer(string='Sheets/Pack')
    tn_weight = fields.Float(string='Weight(Grams)')
    tn_weight_uom = fields.Float(string='Weight Per UoM(Grams)')
    kg_sht = fields.Float(string='Sheet Count')
    pulls_count = fields.Float(string='Pulls/Sheet Count')
    tr_sheet_count = fields.Integer(string='Sheet Count')
    no_of_rolls_log = fields.Char(string='No of Rolls/Log')
    no_of_clips_log = fields.Char(string='No of Clips/Log')
    kg_sleeve = fields.Char(string='Sleeve')
    kg_print = fields.Char(string='Print')
    kg_pack = fields.Many2one('kg.pack', 'Interfold pack')
    kg_core = fields.Many2one('kg.core', 'Core')
    kg_trrt = fields.Char('TRRT')
    kg_cph = fields.Char('CPH')

    tn_actual_speed = fields.Float(string='Actual Speed(m/min)')
    tn_prod_packs = fields.Float(string='Production(Pack/Min)')
    eff_speed = fields.Char(string='Effective Speed(m/min)')
    eff_pulls_minute = fields.Char(string='Effective Production(pulls/min)')
    eff_prod = fields.Char(string='Effective Production(Log/min)')
    eff_speed_rolls = fields.Char(string='Rolls or Box per Minute')
    pack_per_min = fields.Char(string="Pack Per Min")
    effic = fields.Char(string='Efficiency(%)')
    eff_output_car_shift = fields.Char(string='Effective Output(Carton/Shift)')
    eff_output_caton = fields.Char(string='Effective Output(Carton/Hours)')
    eff_output_car_month = fields.Char(string='Effective Output(Carton/Month)')
    eff_ton_per_month = fields.Char(string='Effective Tonnage per Month')
    pack_mach_speed = fields.Char(string='Packing Machine Speed(Packs/Minute)')
    kg_machine = fields.Many2one('maintenance.equipment', "Machine")

    """###*** Spare Parts ***"""

    spare_cc = fields.Char(string="CC")
    size_dim = fields.Char("Size/Dim")
    brand_make = fields.Char("Brand/Make")
    spare_item_code = fields.Char("Item Code")
    spare_stat = fields.Char("STAT")

    spare_type = fields.Many2one('kg.spare.type', "Type")
    model_no = fields.Char("Model No")
    spare_cat = fields.Char("CAT")
    spare_min_stk = fields.Float("Min STK")
    spare_loc = fields.Char("LOC")
    spare_rop = fields.Char("ROP")
    spare_count_value = fields.Float("Count Value")
    spare_remarks = fields.Text("Remarks")

    def action_open_material_consumption(self):
        return {
            'name': 'Stationary Consumption',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree',
            'res_model': 'stationary.consumption',
            'domain': [('product_id.product_tmpl_id', '=', self.id)],
            'target': 'new'
        }


class ProductProduct(models.Model):
    _inherit = 'product.product'

    # alt_desc = fields.Char(related='product_tmpl_id.alt_desc')
    ply = fields.Float(related='product_tmpl_id.ply')
    thickness = fields.Float(related='product_tmpl_id.thickness')
    reel_width = fields.Float(related='product_tmpl_id.reel_width')
    division_code = fields.Char(related='product_tmpl_id.division_code')
    sup_part_no = fields.Char(srelated='product_tmpl_id.sup_part_no')
    gsm = fields.Float(related='product_tmpl_id.gsm')
    sheet_size = fields.Float(related='product_tmpl_id.sheet_size')
    sheet_length = fields.Float(related='product_tmpl_id.sheet_length')
    origin_country = fields.Many2one(related='product_tmpl_id.origin_country')
    stationary_consumed_qty = fields.Float(string="Consumed Qty", Store=True)
    brand_id = fields.Many2one('product.brand', string="Brand")
    kg_group_id = fields.Many2one('product.group', string="Group")
    sub_group_id = fields.Many2one('product.sub.group', "Sub Group")

    def action_open_material_consumption_product(self):
        return {
            'name': 'Stationary Consumption',
            'type': 'ir.actions.act_window',
            # 'view_type': 'tree',
            'view_mode': 'tree',
            'res_model': 'stationary.consumption',
            'domain': [('product_id', '=', self.id)],
            'target': 'new'
        }
