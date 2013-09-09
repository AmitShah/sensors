    	$(function(){
    	
    		var demos = $('#demos');
	 		$.fn.rendererFactory = function(type){
    			if(type === 100 || type===500 || type === 600 || type ===700){ //temperature based
    				
    					return function(){
							var knob= null; 
							var id = null;
							var elem = null;
							return {'update' :function(event){
												//update time
												var date = new Date(parseFloat(event.timestamp)*1000);
												var time = moment(date).format('h:mm:ss a');
												elem.find('.time').html(time);																																
												knob.updateValue(event.rfidTemperature,100);
											},
									'init': function(rfid){
												id = rfid.tagNum;
												var html = templates['type-'+100]({ id:id, name:rfid.displayName});
												demos.append(html);
												elem = $('#'+id);
												knob = new Knob("#knob-"+id, 100.00, 100.00, 250, 250,'', ['#EA445A','#fee79b','#2da9dc']);											
												knob.updateValue(0.00,100);
											}								
								};
							
							}();//end function and call
				 }else if (type === 400){//motion tag
				 	return function(){
				 		var elem = null;
					 	return{
						  		'init':function(rfid){
						  			id = rfid.tagNum;
									var html = templates['type-'+400]({ id:id, name:rfid.displayName});
									demos.append(html);								
									elem = $('#'+id);
						  		},
						  		'update':function(event){
						  		//update time
									var date = new Date(parseFloat(event.timestamp)*1000);
									var time = moment(date).format('h:mm:ss a');
									elem.find('.time').html(time);				
						  			if(event.statusCode === 62735){
						  				elem.find('.no').removeClass('active');
						  				elem.find('.yes').addClass('active');
						  			}else{
						  				elem.find('.yes').removeClass('active');
						  				elem.find('.no').addClass('active');						  			
						  			}			
						  		}
						  	}
					  }();
				 }
				 else if (type == 300){//switch tag
				 	return function(){
				 		var elem = null;
					 	return{
						  		'init':function(rfid){
						  			id = rfid.tagNum;
									var html = templates['type-'+300]({ id:id, name:rfid.displayName});
									demos.append(html);
									elem = $('#'+id);
									
						  		},
						  		'update':function(event){
    						  		//update time
									var date = new Date(parseFloat(event.timestamp)*1000);
									var time = moment(date).format('h:mm:ss a');
									elem.find('.time').html(time);	
						  			if(event.statusCode === 62730){
						  				elem.find('.off').removeClass('active');
						  				elem.find('.on').addClass('active');
						  			}else{
						  				elem.find('.on').removeClass('active');
						  				elem.find('.off').addClass('active');						  			
						  			}
						  			
						  		}
						  	}
					 }();
				 }
				 else{
					  	return{
					  		'init':function(rfid){
					  		
					  		},
					  		'update':function(event){
					  			
					  		}
					  	}
					};//end case
    			
    			};
    	
    		var templates = {};
    		//initialize variables
    		var uptime = $("#uptime");
    		var demo = $('#demo');
			var knob= new Knob("#knob", 0.00, 0.00, 250, 250,'', ['#EA445A','#fee79b','#2da9dc']);
    		var rfids = {};
    		
    		uptime.html('init');
    		
    		//get rfid meta data
    		var init = function(){
	    		$.ajax({
				  url: "/meta",		
				  dataType: "json",
				  success: function(meta){
				  	meta.sort(function(a,b){
				  		return a.rfidTypeCode - b.rfidTypeCode;
				  	});
				  	for(var m in meta){
				  		rfids[meta[m].tagNum] = $.fn.rendererFactory(meta[m].rfidTypeCode);
				  		rfids[meta[m].tagNum].init(meta[m]);
				  	}
				  	
					meta = null;
				 	start();
				  },
				  error : function(e){
				  	uptime.html('error: ' + e.message);
				  }	  
				});
			};
			
			var handle = function(data){	
				try{
					if(rfids.hasOwnProperty(data.rfidTagNum)){
						rfids[data.rfidTagNum].update(data);
					}				
					/*var date = new Date(parseFloat(data.timestamp)*1000);
					uptime.html(moment(date).fromNow());
					//TODO: handle the different type of sensor states
					if(data.rfidTemperature){
						knob.updateValue(parseFloat(data.rfidTemperature),100);
        			}
        			switch(rfids[data.rfidTagNum].rfidTypeCode){
        				case 300:
        					break;
        				case 400:
        					break;
        			}*/
        		}
        		catch (err){
        			uptime.html('error'+err.message);
        		}
			};
			
			var ws = new WebSocket('ws://localhost:9999/update');
			var start = function(){
				uptime.html("online");
				ws.onopen = function()
			    {
			
				};
			    ws.onmessage = function (event) 
			    { 
			     try{
			     		var buffer = $.parseJSON(event.data);		     		
			     		if(buffer && buffer !== ''){
			     			handle($.parseJSON(buffer));
			     		}
			     		
			       }catch(err)
			       {
				
			       }
	
	
			    };
			    ws.onclose = function()
			    { 
			    	//TODO
			    	//output connection state
			    	uptime.html('offline');
			    	
			    };
		   }//end start
		    
		   	$.ajax({
			  url: "/static/handlebars/template.handlebars",		
			  success: function(t){
			  	$('body').append(t);
			  	$("[type='text/template']").each(function(index,elem){
			  		var jelem = $(elem);
			  		templates[elem.id] = Handlebars.compile(jelem.html());
			  	});
			  	init();
			  },
			  error : function(e){
			  	uptime.html('error retreiving templates');
			  }	  
			});
		})