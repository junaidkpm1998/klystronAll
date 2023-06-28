/** @odoo-module **/
import Registries from 'point_of_sale.Registries';
import {PosGlobalState,Order} from 'point_of_sale.models'
const BookOrders = (PosGlobalState) => class BookOrders extends PosGlobalState {
   async _processData(loadedData) {
  	 await super._processData(...arguments);
  	 this.booking_order = loadedData['booking.order'];
  	 console.log('booked_order',this.booked_orders)
  	 this.booking_order_line = loadedData['book.order.line'];


  	 }
}
Registries.Model.extend(PosGlobalState, BookOrders);
const BookedOrder = (Order) => class BookedOrder extends Order {
    constructor(obj, options) {
    super(...arguments);
        if (options.json) {
            this.booked_orders = options.json.booked_orders || undefined;
            console.log("option json1",this.booked_orders)
            this.book_order = options.json.book_order || false;
                        console.log("option json2",this.book_order)

            this.booked_data = options.json.booked_data || undefined;
                                    console.log("option json23",this.booked_data)

        }
    }

    init_from_JSON(json){
        super.init_from_JSON(...arguments);
        this.booked_orders = json.booked_orders;
                    console.log("init_from_JSON1",this.booked_orders)

        this.book_order = json.book_order;
                            console.log("init_from_JSON2",this.book_order)

        this.booked_data = json.booked_data
                            console.log("init_from_JSON3",this.booked_data)

       }
        export_as_JSON(){
            const json = super.export_as_JSON(...arguments);
            json.booked_orders = this.booked_orders;
                        console.log(json.booked_orders,"export_as_JSON1")

            json.booked_data = this.booked_data;
            console.log(json.booked_data,"export_as_JSON2")
            json.book_order = this.book_order;
            console.log('is_booked',json.book_order)
            return json;
        }
    }
Registries.Model.extend(Order, BookedOrder);

//import { PosGlobalState} from 'point_of_sale.models';
//import Registries from 'point_of_sale.Registries';
//const NewPosGlobalState = (PosGlobalState) => class NewPosGlobalState extends PosGlobalState {
//   async _processData(loadedData) {
//  	 await super._processData(...arguments);
//  	 this.booking_order = loadedData['booking.order'];
//  	 this.booking_order_line = loadedData['book.order.line'];
//  	 }
//}
//Registries.Model.extend(PosGlobalState, NewPosGlobalState);
//const BookedOrder = (Order) => class BookedOrder extends Order {
//    constructor(obj, options) {
//    super(...arguments);
//        if (options.json) {
//            this.booking_order = options.json.booking_order || undefined;
//            console.log("stringoptjson",this.booking_order )
//            this.book_order = options.json.book_order || false;
//                        console.log("string2optjson",this.book_order )
//
//            this.booked_data = options.json.booked_data || undefined;
//                                    console.log("string3optjson",this.booked_data )
//
//        }
//    }
//
//    init_from_JSON(json){
//        super.init_from_JSON(...arguments);
//        this.booking_order = json.booking_order;
//        this.is_booked = json.is_booked;
//        this.booked_data = json.booked_data
//       }
//        export_as_JSON(){
//            const json = super.export_as_JSON(...arguments);
//            json.booking_order = this.booking_order;
//            json.booked_data = this.booked_data;
//            console.log(json.booked_data,"gggg")
//            json.is_booked = this.is_booked;
//            console.log('is_booked',json.is_booked)
//            return json;
//        }
//    }
//Registries.Model.extend(Order, BookedOrder);