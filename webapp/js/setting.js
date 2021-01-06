/* methods prefixed by '_' can be considered as private or protected (called by the other methods of the object or by html handler defined by this class */
class SettingsController{
  /* constructor */
  constructor(){
    console.log('Initialization of SettingsController...');
    this._values={};
    const obj=this;
    var path=BASE_URL+'/templates/settings.html';
    isAdmin=true;
    $.ajax({
        url:path,
        cache:HANDLEBARS_CACHE,
        success:function(data){
            var templateInput={ controller : obj };
            var template=Handlebars.compile(data,{ strict: true });
            $('#content').html(template(templateInput));
            obj._get();
        }
    });
    console.log('SettingsController initialized');
  }
  getResourceKey(){
    return 'settings';
  }
  _showValues(){
    var templateInput={ controller : this };
    $('#settings_values').html(Handlebars.partials['settings_values-partial'](templateInput));
  }
  _cancel(){
    this._get();
  }
  _get(){
    const obj=this;
    console.log('Retrieving settings...');
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
          var sortedLabels=[];
          var unsorted={};
          Object.keys(response).forEach(function(key){
            var value=response[key];
            var index=key.indexOf('.');
            var label;
            if(index<0){
              label=capitalize($.i18n(key));
            }else{
              label=capitalize(key.substring(0,index))+': '+capitalize($.i18n(key.substring(index+1)));
            }
            value['id']=key;
            value['label']=label;
            sortedLabels[sortedLabels.length]=label;
            unsorted[label]=value;
          });
          sortedLabels.sort();
          sortedLabels.forEach(function(label){
            obj._values[label]=unsorted[label];
          });
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