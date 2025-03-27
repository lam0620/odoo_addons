odoo.define("sprite.custom", function (require) {
    "use strict";

    // Tool for patch modules
    const { patch } = require("@web/core/utils/patch");

    // Modules that need to patched
    var { CalendarCommonRenderer } = require('@web/views/calendar/calendar_common/calendar_common_renderer');
    var { CalendarModel } = require('@web/views/calendar/calendar_model');

    // Utils using in this file
    var { renderToString } = require("@web/core/utils/render");
    var { getColor } = require("@web/views/calendar/colors");
    var { loadCSS, loadJS } = require("@web/core/assets");

    const everybodyId = 'all';

    // For patch CalendarCommonRenderer
    patch(CalendarCommonRenderer.prototype, "Patch for CalendarCommonRenderer", {
        // Extends --------------------------------------------------------------
        async setup() {
            // // Make sure load files before calling parent.setup()
            // await this.loadJsFiles();
            // await this.loadCssFiles();
            // if (this.__owl__.patched){
            //     this.__owl__.patched.push(()=>{
            //         var fcApi = this.fc.api;
            //         // Re-render resource calendar when change the resource input
            //         fcApi.refetchResources();
            //     });
            // }

            // Call parent method
            await this._super(...arguments);
        },
        async loadJsFiles(){
            const files = [
                'sprite_fullcalendar/static/lib/packages/core/main.js',
                'sprite_fullcalendar/static/lib/packages/interaction/main.js',   
                'sprite_fullcalendar/static/lib/packages/luxon/main.js',            
                'sprite_fullcalendar/static/lib/packages/daygrid/main.js',
                'sprite_fullcalendar/static/lib/packages/timegrid/main.js',

                'sprite_fullcalendar/static/lib/premium/resource-common/main.js',
                'sprite_fullcalendar/static/lib/premium/resource-daygrid/main.js',
                'sprite_fullcalendar/static/lib/premium/resource-timegrid/main.js',

            ];
            for (const file of files) {
                await loadJS(file);
            }
        },
        async loadCssFiles() {
            const files = [
                'sprite_fullcalendar/static/src/custom.css',
                'sprite_fullcalendar/static/lib/packages/daygrid/main.css',
                'sprite_fullcalendar/static/lib/packages/timegrid/main.css',

            ];
            for (const file of files) {
                await loadCSS(file);
            }
        },
        calResources: function () {
            var resources = [];
            Object.values(this.props.model.data.filterSections.partner_ids.filters).map((r) => {
                if (r.active == true) {
                    var id = r.value;
                    var title = r.label;

                    // Exist in resources array or not
                    var exist = false;
                    for (var i = 0; i < resources.length; i++) {
                        if (resources[i].id == id) {
                            exist = true;
                            break;
                        }
                    }

                    // Add to resources if no exist and is is not 'all' (Everybody's calendar) (don't show title to col if check 'all')
                    if (!exist && id !='all') {
                        resources.push({
                            id: id,
                            title: title
                        });
                    }
                }
            });
            return resources;
        },
        get options() {
            var self = this;

            // Call load files here to make sure files are available to use
            // this option() method is called in parent.setup() (called at this setup method ) so that don't call at this setup()
            this.loadJsFiles();
            this.loadCssFiles();
            if (this.__owl__.patched){
                this.__owl__.patched.push(()=>{
                    var fcApi = this.fc.api;
                    // Re-render resource calendar when change the resource input
                    fcApi.refetchResources();
                });
            }

            var options = this._super();

            // Just for Spa calendar
            if (this.props.model.meta.resModel === 'spa.booking') {
                if (this.props.model.scale == 'day') {
                    // Change the default view of day to resource timeline
                    //options.defaultView = 'resourceTimelineDay';
                    options.defaultView = 'resourceTimeGridDay';
                    //options.plugins = [ 'interaction', 'resourceDayGrid', 'resourceTimeGrid' ];
                    // Add plugin "luxon" to correct time in start date box. If no, time = local time + 7
                    options.plugins = [ 'luxon','interaction', 'resourceTimeGrid' ];
                }
                // Fix show correct time in start date box. If no, time = local time + 7
                //options.timeZone = 'Asia/Ho_Chi_Minh';
                
                options.resourceLabelText = 'Resources';
                options.resources = (_, successCb) => {
                    var resources = this.calResources();
                    //console.log("++++ Resources: ");
                    //console.log(resources);
                    successCb(resources);
                };
                options.resourceAreaWidth = '200px';
                options.schedulerLicenseKey = 'GPL-My-Project-Is-Open-Source';
            }

            return options;
        },
        convertRecordToEvent(record) {
            var event = this._super(record);
            // Bind the resource information to event of calendar
            if (record.rawRecord.partner_ids.length > 0){
                event.resourceId = record.rawRecord.partner_ids[0];
            } else {
                event.resourceId = everybodyId;// Everybody
            }
            return event;
        },
        fcEventToRecord(event) {
            //debugger;
            var record = this._super(event);

            // Exist  if click for creating new booking
            if (event.resource) {
                // Bind the resource information to record from event
                if (event.resource._resource.id === everybodyId){
                    record.partner_ids = []; // Everybody
                } else {
                    record.partner_ids = [parseInt(event.resource._resource.id)];
                }
            }

            // Exist if drag and drop event
            if (event._def && !this.props.model.records[event.id].rawRecord.partner_ids.includes(parseInt(event._def.resourceIds[0]))) {
                record.partner_ids = event._def.resourceIds;
            }
            return record;
        },


        // Override ----------------------------------------------------
        // Render color of each event that is displaying on Calendar view mode
        onEventRender(info) {
            const { el, event } = info;
            el.dataset.eventId = event.id;
            el.classList.add("o_event", "py-0");
            const record = this.props.model.records[event.id];

            if (record) {
                // This is needed in order to give the possibility to change the event template.
                const injectedContentStr = renderToString(this.constructor.eventTemplate, {
                    ...record,
                    startTime: this.getStartTime(record),
                });
                const domParser = new DOMParser();
                const { children } = domParser.parseFromString(injectedContentStr, "text/html").body;
                // Namnd fix
                // el.querySelector(".fc-content").replaceWith(...children); // el.querySelector(".fc-content") may be not exist
                var fcContent = el.querySelector(".fc-content");
                if (fcContent) {
                    fcContent.replaceWith(...children);
                } else {
                    var fcContent = el.querySelector(".fc-title-wrap");
                    if (fcContent) {
                        fcContent.replaceWith(...children);
                    }
                }
                const color = getColor(record.colorIndex);
                if (typeof color === "string") {
                    el.style.backgroundColor = color;
                } else if (typeof color === "number") {
                    el.classList.add(`o_calendar_color_${color}`);
                } else {
                    el.classList.add("o_calendar_color_0");
                }

                if (record.isHatched) {
                    el.classList.add("o_event_hatched");
                }
                if (record.isStriked) {
                    el.classList.add("o_event_striked");
                }
            }
            // Comment by Lam: this because bg color below is not work
            // if (!el.querySelector(".fc-bg")) {
            //     const bg = document.createElement("div");
            //     bg.classList.add("fc-bg");
            //     el.appendChild(bg);
            // }

            // Add by Lam
            // Check customer type and set correct color.
            // Classes defined in custom.css            
            if (record && record.rawRecord && record.rawRecord.customer_type) {
                const customer_type = record.rawRecord.customer_type;
                el.classList.add(`o_calendar_color_${customer_type}`);

                if (record.rawRecord.location && record.rawRecord.location === 'home') {
                    el.classList.add("o_calendar_color_home");
                }
            }
            if (record && record.rawRecord && record.rawRecord.state) {
                const state = record.rawRecord.state;
                el.classList.add(`o_calendar_color_${state}`);
            }            
            //End
        }
    });

    // For patch CalendarModel
    patch(CalendarModel.prototype, "Patch for CalendarModel", {
        // Extends --------------------------------------------------------------
        setup() {
        	//debugger;
            this._super(...arguments);
        },
        buildRawRecord(partialRecord, options = {}) {
            var data = this._super(partialRecord, options = {});
            if (partialRecord.partner_ids) {
                data['partner_ids'] = partialRecord.partner_ids;
            }
            return data;
        },
        makeContextDefaults(rawRecord) {
            var context = this._super(rawRecord);
            if (rawRecord['partner_ids'] !== undefined) {
                context['default_partner_ids'] = rawRecord['partner_ids'];
            }
            return context;
        },
	    /**
	     * @overwrite
	     */
	    fetchFilters(resModel, fieldNames) {
	    	//debugger;
	    	var company_ids = this.user.context.allowed_company_ids;	    

	    	// 20230323 Add by Lam. Add a condition "["company_id", "=", company_id]" for "salon.booking.filter"
	    	//return this.orm.searchRead(resModel, [["user_id", "=", this.user.userId]], fieldNames);
	    	if (resModel === "salon.booking.filter") {
	        	return this.orm.searchRead(resModel, [["user_id", "=", this.user.userId],["company_id", "in", company_ids]], fieldNames);
	        } else {
	        	return this.orm.searchRead(resModel, [["user_id", "=", this.user.userId]], fieldNames);
	        }
	    }        	
    });


});
