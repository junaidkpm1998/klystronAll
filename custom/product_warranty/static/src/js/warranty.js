odoo.define("product_warranty.product_warranty", function(require){

    var publicWidget = require('web.public.widget');

    var rpc = require('web.rpc');
    publicWidget.registry.PublicWidgetProductWarranty = publicWidget.Widget.extend({
        selector : ".oe_empty",
        events:{
        'change #invoice_id' : '_onShowProduct',
//        'change #invoice_id' : '_onShowProduct',
//        'change #invoice_id' : '_onShowPartner',
//        'change #invoice_id' : '_onShowReqDate',
//        'change #invoice_id' : '_onShowPurDate',
//        'change #invoice_id' : '_onShowExpDate',
        'change #prod_id' : '_onShowLot'
        },


//            $( "#invoice_id" ).change(function() {
//             alert("The text has been changed.");
////                console.log("oooo");
////                '_onShowLot';
//            });

        _onShowProduct : function(ev){
            var inv_id = ev.target.value
            this.$("#prod_id").empty();

            rpc.query({
             model: "warranty.model",
             method: 'get_product',
             args: [,inv_id]
             }).then(function(data){

                data.forEach(function(result){

                console.log('data', data)
                console.log('result', result)
                 var product_final = Object.values(data)
                 var product_id = Object.keys(result)
                 var x = Object.values(product_final)
                    for (let i = 0; i < data.length; i++) {

                        $('#prod_id').append($("<option><option/>").attr("value",product_id).text(x[i][product_id]));
                    }
                    })
//                $.each(data, function(key, value) {
//                     $('#prod_id').append($("<option></option>").attr("value", key).text([][value]));
//                });

             });
            },
              _onShowLot : function(ev){
                    var prod_id = ev.target.value
                    this.$("#lot").empty();
                    console.log(prod_id,"prod_id is")
                    rpc.query({
                     model: "warranty.model",
                     method: 'get_lot',
                     args: [,prod_id ]
                     }).then(function(data){


                 data.forEach(function(result){

                 var lot_final = Object.values(data)
                 var product_id = Object.keys(result)
                 var val = Object.values(lot_final)
//                    for (let i = 0; i < data.length; i++) {

                        $('#lot_id').append($("<option><option/>").attr("value",product_id).text(val[0][product_id]));
//                    }
                    })
                    console.log("lot function called")
             });
            }
});
});
