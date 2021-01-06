/* methods prefixed by '_' can be considered as private or protected (called by the other methods of the object or by html handler defined by this class */
class DetectionFiltersController{
  /* constructor */
  constructor(){
    console.log('Initialization of DetectionFiltersController...');
    this._values={};
    this._availableHosts={};
    const obj=this;
    var path=BASE_URL+'/templates/detection_filters.html';
    isAdmin=true;
    $.ajax({
        url:path,
        cache:HANDLEBARS_CACHE,
        success:function(data){
            var templateInput={ controller : obj };
            var template=Handlebars.compile(data,{ strict: true });
            $('#content').html(template(templateInput));
            obj._get();
            obj._getAvailableHosts();
            resetGetAvailableHosts();
        }
    });
    console.log('DetectionFiltersController initialized');
  }
  getResourceKey(){
    return 'filters';
  }
  _showValues(){
    var templateInput={ controller : this, values : this._values };
    $('#filters_values').html(Handlebars.partials['detection_filters_values-partial'](templateInput));
  }
  _showAvailableHosts(){
    var templateInput={ controller : this, availableHosts : this._availableHosts };
    $('#filters_available_hosts').html(Handlebars.partials['detection_filters_available_hosts-partial'](templateInput));
  }
  _remove(id){
    if(!isAdmin){
      return;
    }
    if(!isValid(id)){
      // console.log('Cannot remove, id is not valid');
      return;
    }
    delete this._values[id];
    this._showValues();
  }
  _add(id,comment){
    if(!isAdmin){
      return;
    }
    if(!isValid(id)){
      id=$('#filter_id').val();
      comment=$('#filter_value').val();
    }
    if(!isValid(id)){
      console.log('Cannot add, id is not valid');
      return;
    }
    // console.log('Adding: '+id);
    if(isValid(comment)){
      this._values[id]=comment;
    }
    this._showValues();
  }
  _addAvailableHost(index){
    const host=this._availableHosts[index];
    const mac=host['mac'];
    if (isValid(mac)&&mac.length>0){
      var comment = host['ipv4'];
      var value=host['hostname'];
      if (value&&value.length>0){
        comment+=', '+value;
      }
      value=host['vendor'];
      if (value&&value.length>0){
        comment+=', '+value;
      }
      this._add(mac,comment);
    }
  }
  _edit(id){
    if(!isAdmin){
      return;
    }
    if(!isValid(id)){
      // console.log('Cannot edit, id is not valid');
      return;
    }
    // console.log('Editing: '+id);
    $('#filter_id').val(id);
    $('#filter_value').val(this._values[id]);
  }
  _cancel(){
    this._get();
  }
  _get(){
    const obj=this;
    console.log('Retrieving filters...');
    this._values={};
    jQuery.ajax({
      type:'GET',
      url:REST_BASE_URL+'/'+obj.getResourceKey(),
      dataType:'json',
      async:true,
      accept:'application/json',
      success:function(response){
        // console.log("Response: "+JSON.stringify(response));
        if(isValid(response)){
          obj._values=response;
        }
      },
      error:function(x,status,error){
        handleAjaxError(x,status,error);
      },
      complete:function(){
        obj._showValues();
      }
    });
  }
  _getAvailableHosts(){
    const obj=this;
    console.log('Retrieving available hosts...');
    this._availableHosts={};
    jQuery.ajax({
      type:'GET',
      url:REST_BASE_URL+'/'+obj.getResourceKey()+'?available',
      dataType:'json',
      async:true,
      accept:'application/json',
      success:function(response){
        // console.log("Response: "+JSON.stringify(response));
        if(isValid(response)){
          obj._availableHosts=response;
        }
      },
      error:function(x,status,error){
        handleAjaxError(x,status,error);
      },
      complete:function(){
        obj._showAvailableHosts();
      }
    });
  }
  _save(){
    if(!isAdmin){
      return;
    }
    const obj=this;
    var json;
    if(isValid(this._values)){
      json=JSON.stringify(this._values);
    }else{
      json='{ }';
    }
    // console.log('JSON: '+json);
    jQuery.ajax({
      type:"POST",
      url:REST_BASE_URL+'/'+obj.getResourceKey(),
      async:true,
      contentType:'application/json',
      dataType: 'json',
      data:json,
      success:function(response){
        // console.log("Response: "+JSON.stringify(response));
      },
      error:function(x){
        handleValidationError(obj.getResourceKey(),x);
      }
    });
  }
}
var getAvailableHostsId=null;
function resetGetAvailableHosts(){
  if(getAvailableHostsId!=null){
    clearTimeout(getAvailableHostsId);
  }
  console.log('Resetting getAvailableHosts timer');
  getAvailableHostsId=setTimeout(getAvailableHosts,30*1000);
}
function getAvailableHosts(){
  if(controller instanceof DetectionFiltersController){
    controller._getAvailableHosts();
  }
  resetGetAvailableHosts();
}
