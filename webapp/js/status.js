/* methods prefixed by '_' can be considered as private or protected (called by the other methods of the object or by html handler defined by this class */
class StatusController{
  /* constructor */
  constructor(){
    console.log('Initialization of StatusController...');
    this._values={};
    const obj=this;
    var path=BASE_URL+'/templates/status.html';
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
    console.log('StatusController initialized');
  }
  getResourceKey(){
    return 'app/status';
  }
  _showValues(){
    var templateInput={ controller : this, values : this._values };
    console.log(this._values);
    $('#status_values').html(Handlebars.partials['status_values-partial'](templateInput));
  }
  _get(){
    const obj=this;
    console.log('Retrieving status...');
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
        obj._values={};
        handleAjaxError(x,status,error);
      },
      complete:function(){
        obj._showValues();
      }
    });
  }
}