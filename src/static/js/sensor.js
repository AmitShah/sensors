    	$(function(){
    	
    		var demos = $('#demos');
    		$.fn.rendererFactory = function(type){
    			if(type === 100 || type===500 || type === 600 || type ===700){ //temperature based
    				
    					return function(){
							var knob= null; 
							var id = null;
							var elem = null;				
							var max=25;
							var min = -25;			
							return {'update' :function(event){
												//update time
												var date = new Date(parseFloat(event.timestamp)*1000);
												var time = moment(date).format('h:mm:ss a');
												elem.find('.time').html(time);																																
												knob.updateValue(event.rfidTemperature,100,max,min);
											},
									'init': function(rfid){
												id = rfid.tagNum;
												var html = templates['type-'+100]({ id:id, name:rfid.displayName,time:'not reported'});
												demos.append('<li class="list-group-item">'+html+'</li>');
									
												elem = $('#'+id);
												knob = new Knob("#knob-"+id, min, 100.00, 250, 250,'', ['#EA445A','#fee79b','#2da9dc'],max,min);											
												knob.updateValue(0.00,100,max,min);												
											}								
								};
							
							}();//end function and call
				 }else if (type === 400){//motion tag
				 	return function(){
				 		var elem = null;
					 	return{
						  		'init':function(rfid){
						  			id = rfid.tagNum;
									var html = templates['type-'+400]({ id:id, name:rfid.displayName,time:'not reported'});
									demos.append('<li class="list-group-item">'+html+'</li>');																	
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
									var html = templates['type-'+300]({ id:id, name:rfid.displayName, time:'not reported'});
									demos.append('<li class="list-group-item">'+html+'</li>');
									elem = $('#'+id);
									
						  		},
						  		'update':function(event){
    						  		//update time
									var date = new Date(parseFloat(event.timestamp)*1000);
									var time = moment(date).format('h:mm:ss a');
									elem.find('.time').html(time);	
						  			if(event.statusCode === 62730){
						  				elem.find('.off').removeClass('rfid-active');
						  				elem.find('.on').addClass('rfid-active');
						  			}else{
						  				elem.find('.on').removeClass('rfid-active');
						  				elem.find('.off').addClass('rfid-active');						  			
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
			var rfidMeta = {};
    		var rfids = {};
    		var filter = "none";
    		
	 		uptime.html('init');
    		
    		//get rfid meta data
    		var init = function(){
	    		$.ajax({
				  url: "/rfids",	
				  method:"POST",	
				  dataType: "json",
				  success: function(meta){
				  	for(var m in meta){
				  		rfidMeta[meta[m].tagNum] = meta[m]; 
				  	}
					meta = null;
				 	start();
				  },
				  error : function(e){
				  	uptime.html('error: ' + e.message);
				  }	  
				});
			};
			var emptyRfidArea = true;
			var handle = function(data){	
				try{
					if((filter=== "none" || data.deviceID === filter) && data.hasOwnProperty('rfidTagNum')){
						if(!rfids.hasOwnProperty(data.rfidTagNum)){
							if(emptyRfidArea){
								emptyRfidArea = false;
								demos.empty();
							}
							rfids[data.rfidTagNum] = $.fn.rendererFactory(rfidMeta[data.rfidTagNum].rfidTypeCode);						
							rfids[data.rfidTagNum].init(rfidMeta[data.rfidTagNum]);
						}
						//update the rfid values	
						rfids[data.rfidTagNum].update(data);
																
					}
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
					  uptime.html("socket error:"+err.message);
			       }
			    };
			    ws.onclose = function()
			    { 			    	
			    	uptime.html('offline');
			    };
		   }//end start
		    
		   $.ajax({
			  url: "/devices",		
			  dataType: "json",
			  method: "POST",
			  success: function(data){			  	
			  	var deviceList = $('#devices');
			  	for(var d in data){
			  		deviceList.append('<li><a href="#" id="filter_'+data[d].deviceID+'">'+data[d].deviceID+'</a></li>');
			  	}			  				  	
			  	//device filter handler			
				deviceList.delegate('a', 'click', function(e){
					var elem = $(this);
					$('#devices li').removeClass('active');
					elem.parent().addClass('active');
					filter = elem.html();
					e.preventDefault();
				});
			  	
			  },
			  error : function(e){
			  	uptime.html('error retreiving templates');
			  }	  
			});

			
			
		    
		    //get handlebar templates
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