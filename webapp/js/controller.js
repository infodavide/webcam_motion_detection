/* methods prefixed by '_' can be considered as private or protected (called by the other methods of the object or by html handler defined by this class */
class AbstractController{
  /* constructor */
  constructor(){
  }
  /* toggle the entity view or form */
  /* id: the identifier of the entity or null */
  /* viewId: the div to fill with the generated view or form */
  /*
   * editable: the boolean describing if a view or an edition form must be
   * created
   */
  /* add: the boolean describing if the specified entity must be cloned or added */
  edit(id,viewId,editable,add){
    var view=$('#'+viewId);
    if(isValid(this.currentViewId)&&(this.currentViewId!==viewId||this.currentViewMode!=editable)){
      var previousView=$('#'+this.currentViewId);
      previousView.hide();
      previousView.html('');
      this.currentViewId=null;
    }
    if(view.is(':visible')){
      view.hide();
      view.html('');
      return;
    }
    // request
    this.currentViewId=viewId;
    this.currentViewMode=editable;
    if(isValid(id)){
      var obj=this;
      this.get(id,function(response){
        if(isValid(add)&&add){
          response.id=undefined;
        }
        obj._showForm(response,view,editable);
      });
    }else{
      this._showForm({},view,editable);
    }
  }
  /* return the resource path of the REST service for the entity */
  getResourcePath(){
    return '<undefined>';
  }
  /* return the resource key used to prefix the HTML identifiers */
  getResourceKey(){
    return '<undefined>';
  }
  /* return the URL */
  /* id: the identifier of the entity */
  getServiceURL(id){
    var serviceUrl=REST_BASE_URL+'/'+this.getResourcePath()+'/';
    if(isValid(id)){
      serviceUrl+=id;
    }
    return serviceUrl;
  }
  /* retrieves the entity using its identifier */
  /* id: the identifier of the entity to retrieve */
  /* callback: the callback function invoked on response */
  get(id,callback){
    var obj=this;
    jQuery.ajax({
      type:'GET',
      url:obj.getServiceURL(id),
      dataType:'json',
      async:true,
      accept:'application/json',
      contentType:'application/json',
      success:function(response){
        // console.log("Response: "+JSON.stringify(response));
        if(callback!=null){
          callback(response);
        }
      },
      error:function(x,status,error){
        handleAjaxError(x,status,error);
      }
    });
  }
  /* deletes the entity using its identifier */
  /* id: the identifier of the entity to remove */
  remove(id){
    var obj=this;
    jQuery.ajax({
      type:'DELETE',
      url:obj.getServiceURL(id),
      async:true,
      success:function(response){
        // console.log('Response: '+JSON.stringify(response));
        loadHealth(true,function(){obj.search(function(a){obj._showView(a);})});
      },
      error:function(x,status,error){
        handleAjaxError(x,status,error);
      }
    });
  }
  /* saves the entity previously edited using the specific form */
  /* id: the identifier of the entity to save or undefined to add a new one */
  /* viewId: the div associated to the form */
  save(id, viewId){
    var obj=this;
    jQuery.ajax({
      type:"POST",
      url:obj.getServiceURL(id),
      async:true,
      contentType:'application/json; charset=UTF-8',
      data:JSON.stringify(this._formData()),
      dataType:'text',
      success:function(response){
        // console.log("Response: "+JSON.stringify(response));
        if(isValid(id)){
          $('#'+viewId).hide();
          obj.search(function(a){obj._showView(a);});
        }else{
          $('#'+viewId).hide();
          loadHealth(true,function(){obj.search(function(a){obj._showView(a);})});
        }
      },
      error:function(x){
        handleValidationError(obj.getResourceKey(),x);
      }
    });
  }
  /* search the entities */
  /* callback: callback method invoked asynchronously when response is received */
  search(callback){
    // request
    var obj=this;
    jQuery
        .ajax({
          type:'GET',
          url:REST_BASE_URL+'/'+obj.getResourcePath()+'/',
          dataType:'json',
          async:true,
          accept:'application/json',
          contentType:'application/json',
          success:function(response){
            // console.log('Response: '+JSON.stringify(response));
            if(callback!=null){
              callback(response);
            }
          },
          error:function(x,status,error){
            handleAjaxError(x,status,error);
          }
        });
  }
}