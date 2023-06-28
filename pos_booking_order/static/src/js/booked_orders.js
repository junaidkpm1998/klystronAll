odoo.define('pos_booking_order.BookedOrdersWidget', function(require) {
  'use strict';
  const PosComponent = require('point_of_sale.PosComponent');
   const ProductScreen = require('point_of_sale.ProductScreen');
   const { useListener } =require("@web/core/utils/hooks");
   const Registries = require('point_of_sale.Registries');
   var rpc = require('web.rpc');
   var core = require('web.core');
   var Qweb = core.qweb;
   const { onMounted, onWillUnmount, useState } = owl;
   class BookedOrdersWidget extends PosComponent {
       setup(){
           super.setup();
           useListener('click-confirm', this._Confirm);

           console.log('thisenv-------',this)

       }
  _Confirm(ev){
            var self = this
            var $current = $(ev.explicitOriginalTarget);
            var pos = $current.closest('#confirm_order').attr('order');
            console.log(pos,"pos")
            var data = this.env.pos.booking_order
            console.log(data,"data")
            var lines = this.env.pos.booking_order_line
            console.log(lines,"linessssss")
            data.forEach(function(datas){
                console.log('forEach',datas)
                if (datas.id==pos){
                    lines.forEach(function(item){
                        console.log('item=------ ',item)
                        if (item.order_id[0]==datas.id){
                             var product = self.env.pos.db.get_product_by_id(item['product_id'][0])
                             console.log('product----',product)
                             var qty = item['qty']
                             self.env.pos.get_order().add_product(product,{quantity: qty})
                       }
                   });
                var partner_id = datas.partner_id[0]
                console.log(partner_id,"pppppppp")
                self.env.pos.get_order().set_partner(self.env.pos.db.get_partner_by_id(partner_id));
                self.env.pos.selectedOrder.is_booked = true
                self.env.pos.selectedOrder.booked_data = datas;
                  console.log( self.env.pos.selectedOrder.booked_data,"jjjjjjjjjjj")
                self.showScreen('ProductScreen');
               }
            });

        }

       back() {
                console.log('thisenv-------',this)

           this.showScreen('ProductScreen');
       }
   };
 BookedOrdersWidget.template = 'BookedOrdersWidget';
 Registries.Component.add(BookedOrdersWidget);
 return BookedOrdersWidget;
});