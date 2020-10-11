/* methods prefixed by '_' can be considered as private or protected (called by the other methods of the object or by html handler defined by this class */
class DetectionFiltersController{
  /* constructor */
  constructor(){
    console.log('Initialization of DetectionFiltersController...');
    $('#content').html('<div id="filters_content"></div>');
    this._get();
  }
  getResourceKey(){
    return 'filters';
  }
  _showValues(){
    var content='<div style="margin-top:16px;"><h1 data-i18n="filters"></h1><p data-i18n="filters_description"></p>';
    var disabled;
    if(isAdmin){
      disabled=false;
      content+='<form id="filters_form" onsubmit="controller._save();return false;">';
    }else{
      disabled=true;
    }
    content+='<div class="row row-header">';
    content+='<div class="column col-lg-2 col-header"></div>';
    content+='<div class="column col-lg-5 col-header" data-i18n="mac-address"></div>';
    content+='<div class="column col-lg-5 col-header" data-i18n="comment"></div>';
    content+='</div>';
    if(isAdmin){
      content+='<div class="row">';
      content+='<div class="column col-lg-2" data-i18n="[title]save">';
      content+='<a id="btn_save_filter" class="save-icon clickable d-none d-lg-block d-xl-block" data-i18n="[title]save" onclick="controller.add();"></a>';
      content+='</div>';
      content+='<div class="column col-lg-5" data-i18n="[title]mac_address_like">';
      var options=buildInputOptions('filter_mac_address','',false,disabled,17,17);
      options.pattern="^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$";
      content+=buildInput($.i18n('mac_address'), '', options);
      content+='</div>';
      content+='<div class="column col-lg-5" data-i18n="[title]comment">';
      options=buildInputOptions('filter_comment','',false,false,0,128);
      content+=buildInput($.i18n('comment'), '', options);
      content+='</div>';
      content+='</div>';
    }
    content+='<div id="filters_div">';
    console.log('Listing filters...');
    if(isValid(this._values)){
      for(const key in this._values){
        content+='<div class="row">';
        content+='<div class="column col-lg-2">';
        if(isAdmin){
          content+='<a id="btn_edit_filter_'+key+'" class="edit-icon clickable d-none d-lg-block d-xl-block" data-i18n="[title]edit" onclick="controller.edit(\''+key+'\')"></a>';
          content+='<a id="btn_delete_filter_'+key+'" class="delete-icon clickable" data-i18n="[title]delete" data-toggle="modal" data-callback="controller.remove(\''+key
            +'\')" data-i18n="[data-title]confirm_deletion" data-message="delete '+key+'?" data-target="#confirmation_modal"></a>';
        }
        content+='</div>';
        content+='<div class="column col-lg-5">'+key+'</div>';
        content+='<div class="column col-lg-5">'+this._values[key]+'</div>';
        content+='</div>';
      }
    }else{
     content+='<div class="row"><div class="column col-lg-12" data-i18n="no_filter"></div></div>';
    }
    content+='</div>';
    if(isAdmin){
      content+='<div style="margin-top:16px;">';
      content+='<button type="submit" id="btn_submit_filters" class="btn btn-primary mb-2" data-i18n="save"></button>';
      content+='<button id="btn_cancel_filters" class="btn btn-primary mb-2" onclick="controller._cancel();" data-i18n="cancel"></button>';
      content+='</div>';
      content+='</form>';
    }
    content+='</div>';
    content+='<div style="margin-top:15px;"><h1 data-i18n="available_hosts"></h1>';
    content+='<div class="row row-header">';
    content+='<div class="column col-lg-2 col-header"></div>';
    content+='<div class="column col-lg-4 col-header" data-i18n="mac-address"></div>';
    content+='<div class="column col-lg-6 col-header" data-i18n="information"></div>';
    content+='</div>';
    content+='<div id="available_hosts_div"></div>';
    content+='</div>';
    $('#filters_content').html(content);
    this._getAvailableHosts();
  }
  _showAvailableHosts(values){
    console.log('Listing available hosts...');
    var content='';
    if(isValid(values)){
      for(const value of values){
        var key=value['mac'];
        if(!isValid(key)){
          key='N/A';
        }
        const hostname=value['hostname'];
        content+='<div class="row">';
        content+='<div class="column col-lg-2">';
        if(isAdmin){
          if(isValid(hostname)){
            content+='<a id="btn_add_host_'+key+'" class="add-icon clickable d-none d-lg-block d-xl-block" data-i18n="[title]add" onclick="controller.add(\''+key+'\',\''+hostname+'\')"></a>';
          }else{
            content+='<a id="btn_add_host_'+key+'" class="add-icon clickable d-none d-lg-block d-xl-block" data-i18n="[title]add" onclick="controller.add(\''+key+'\')"></a>';
          }
        }
        content+='</div>';
        content+='<div class="column col-lg-4">'+key+'</div>';
        content+='<div class="column col-lg-6"><span data-i18n="ip"></span>: '+value['ipv4'];
        if(isValid(hostname)){
          content+='</br><span data-i18n="name"></span>: '+hostname;
        }
        const vendor=value['vendor'];
        if(isValid(vendor)){
          content+='</br><span data-i18n="vendor"></span>: '+vendor;
        }
        content+='</div>';
        content+='</div>';
      }
    }else{
      content+='<div class="row"><div class="column col-lg-12" data-i18n="no_host"></div></div>';
    }
    $('#available_hosts_div').html(content);
  }
  remove(id){
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
  add(key,comment){
    if(!isAdmin){
      return;
    }
    if(!isValid(key)){
      key=$('#filter_mac_address').val();
      comment=$('#filter_comment').val();
    }
    if(!isValid(key)){
      console.log('Cannot add, key is not valid');
      return;
    }
    // console.log('Adding: '+key);
    if(isValid(comment)){
      this._values[key]=comment;
    }
    this._showValues();
  }
  edit(id){
    if(!isAdmin){
      return;
    }
    if(!isValid(id)){
      // console.log('Cannot edit, id is not valid');
      return;
    }
    // console.log('Editing: '+id);
    $('#filter_mac_address').val(id);
    $('#filter_comment').val(this._values[id]);
  }
  _cancel(){
    this._get();
  }
  _get(){
    const obj=this;
    jQuery.ajax({
      type:'GET',
      url:REST_BASE_URL+'/'+obj.getResourceKey(),
      dataType:'json',
      async:true,
      accept:'application/json',
      success:function(response){
        // console.log("Response: "+JSON.stringify(response));
        obj._values={};
        if(isValid(response)){
          obj._values=response;
        }
        obj._showValues();
      },
      error:function(x,status,error){
        handleAjaxError(x,status,error);
      }
    });
  }
  _getAvailableHosts(){
    const obj=this;
    console.log('Retrieving available hosts...');
    jQuery.ajax({
      type:'GET',
      url:REST_BASE_URL+'/'+obj.getResourceKey()+'?available',
      dataType:'json',
      async:true,
      accept:'application/json',
      success:function(response){
        // console.log("Response: "+JSON.stringify(response));
        obj._showAvailableHosts(response);
      },
      error:function(x,status,error){
        handleAjaxError(x,status,error);
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
