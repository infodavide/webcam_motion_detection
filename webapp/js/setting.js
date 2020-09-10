/* methods prefixed by '_' can be considered as private or protected (called by the other methods of the object or by html handler defined by this class */
class SettingController extends AbstractController{
  static buildParameterTypeInputOptions(fieldId,required,disabled){
    var options=buildInputOptions(fieldId,'select',required,disabled);
    options.items=[];
    options.items.push(buildSelectOption('STRING','Text'));
    options.items.push(buildSelectOption('PASSWORD','Password'));
    options.items.push(buildSelectOption('INTEGER','Integer'));
    options.items.push(buildSelectOption('DOUBLE','Double'));
    options.items.push(buildSelectOption('BOOLEAN','Boolean'));
    options.items.push(buildSelectOption('DATE','Date'));
    return options;
  }
  /* constructor */
  constructor(){
    super();
  }
  /* initialize the main view */
  init(){
    console.log('Initialization of SettingController...');
    var obj=this;
    this.search(function(a){obj._showView(a);});
  }
  /* return the resource path of the REST service */
  getResourcePath(){
    return 'app/param';
  }
  /* return the resource key used to prefix the HTML identifiers */
  getResourceKey(){
    return 'set';
  }
  /* returns the HTML view of one row of the list of settings */
  /* item: the object describing the setting and coming from the REST service */
  _getHtmlRow(item){
    var viewRowId='set_view_'+item.id;
    var content='<div class="column col-lg-3 clickable" title="The name of the setting" onclick="settingController.edit('+item.id
        +',\'new_set_view\',true,false)" ondblclick="settingController.edit('+item.id+',\'new_set_view\',true,true)">'+item.name+'</div>';
    content+='<div class="column col-lg-5" title="The value of the setting">';
    if(isValid(item.value)){
      content+=item.value;
    }
    content+='</div>';
    content+='<div class="column col-lg-2 text-center" title="The date of the last modification of the setting">'+item.modificationDate+'</div>';
    content+='<div class="column col-lg-2 justify-content-end d-flex">';
    content+='<a id="btn_view_set_'+item.id+'" class="view-icon clickable" title="View details of the setting" onclick="settingController.edit('+item.id+',\''+viewRowId+'\',false)"></a>';
    if(item.editable){
      content+='<a id="btn_edit_set_'+item.id+'" class="edit-icon clickable d-none d-lg-block d-xl-block" title="Edit details of the setting" onclick="settingController.edit('+item.id+',\''+viewRowId+'\',true)"></a>';
      content+='<a id="btn_copy_set_'+item.id+'" class="copy-icon clickable d-none d-lg-block d-xl-block" title="Copy the setting" onclick="settingController.edit('+item.id+',\'set_view_0\',true,true)"></a>';
    }
    if(item.deletable){
      content+='<a id="btn_delete_set_'+item.id+'" class="delete-icon clickable" title="Delete the setting" data-toggle="modal" data-callback="settingController.remove('+item.id
          +')" data-title="Confirm deletion" data-message="<p>Delete the setting '+item.name+' ?</p>" data-target="#confirmation_modal"></a>';
    }
    content+='</div>';
    return content;
  }
  /* builds and shows the view the settings */
  /* response : the response coming from the search or list method */
  _showView(response){
    // console.log(response.length);
    // header
    var content='<h1 style="color: #314190;">Settings</h1>';
    if(response.canAdd){
      content+='<div class="row">';
      content+='<div class="column col-lg-2 col_header"></div>';
      content+='<div class="column col-lg-8 col_header" style="text-align: left;">';
      content+='<button id="btn_add_set" class="btn btn-primary mb-2" onclick="settingController.edit(undefined,\'set_view_0\',true,true)" title="Add a new setting">Add</button>';
      content+='</div>';
      content+='<div class="column col-lg-2 col_header"></div>';
      content+='</div>';
      content+='<div class="row set-view" id="set_view_0" style="display:none;"></div>';
    }
    if(response.totalSize==0){
      content+='<div class="row">';
      content+='<div class="column col-lg-12" title="No setting found">No setting found</div>';
      content+='</div>';
    }else{
      content+='<div class="row row_header">';
      content+='<div class="column col-lg-3 col_header">Name</div>';
      content+='<div class="column col-lg-5 col_header">Value</div>';
      content+='<div class="column col-lg-2 col_header">Modified at</div>';
      content+='<div class="column col-lg-2 col_header">Action(s)</div>';
      content+='</div>';
      // data
      for(var i=0;i<response.results.length;i++){
        var item=response.results[i];
        var viewRowId='set_view_'+item.id;
        content+='<div class="row" id="set_row_'+item.id+'">';
        content+=this._getHtmlRow(item);
        content+='</div>';
        content+='<div class="row set-view" id="'+viewRowId+'" style="display:none;"></div>';
      }
    }
    $('#content').html(content);
  }
  /* builds and shows the HTML view or form */
  /* response: the data of the setting to view or edit */
  /* editable: the boolean describing if a view or an edition form must be created */
  _showForm(response,view,editable){
    var viewId = view.attr('id');
    var content='<div class="column col-lg-1"/>';
    content+='<div class="column col-lg-11" title="The details of the setting">';
    // start of main column
    var useForm=isValid(editable)&&editable;
    var id;
    var builtin;
    if(isValid(response)&&isValid(response.id)){
      builtin=response.builtin;
      id=response.id;
    }else{
      builtin=false;
      id=0;
    }
    if(useForm){
      content+='<form id="set_form" onsubmit="settingController.save(';
      if(id>0){
        content+=id;
      }else{
        content+='undefined';
      }
      content+=',\''+viewId;
      content+='\');return false;">';
    }
    content+=addPropertiesHeader();
    // fields
    content+=addProperty('Builtin','The builtin flag',builtin,editable,buildBooleanInputOptions('set_builtin',true,response.readOnly||builtin));
    content+=addProperty('Read only','The read only flag',response.readOnly,editable,buildBooleanInputOptions('set_readOnly',true,response.readOnly||builtin));
    var options=buildInputOptions('set_name','',true,response.readOnly||builtin,1,48);
    options.pattern="([A-Z-a-z0-9\-_\.])*";
    content+=addProperty('Name','The name of the setting (min 1 characters, max 48 characters)',response.name,editable,options);
    content+=addProperty('Type','The type',response.type,editable,SettingController.buildParameterTypeInputOptions('set_type',true,response.readOnly||builtin));
    if(response.type === 'BOOLEAN'){
      options=buildBooleanInputOptions('set_value',false,response.readOnly);
    }else if(response.type === 'INTEGER'){
      options=buildInputOptions('set_value','number',false,response.readOnly)
    }else if(response.type === 'DOUBLE'){
      options=buildInputOptions('set_value','number',false,response.readOnly)
    }else if(response.type === 'DATE'){
      options=buildInputOptions('set_value','date',false,response.readOnly)
    }else if(response.type === 'PASSWORD'){
      options=buildInputOptions('set_value','password',false,response.readOnly,0,32);
      options.autocomplete=false;
    }else{
      options=buildInputOptions('set_value','',false,response.readOnly,0,1024);
    }
    options.pattern="[A-Z-a-z0-9\-_\.:/\\@,;]*";
    content+=addProperty('Value','The value of the setting (max 32 characters for a password or 1024 characters)',response.value,editable,options);
    if(useForm){
      // noop
    }else{
      content+=addProperty('Registration date','The date of registration',response.creationDate,editable,buildInputOptions('set_creation_date','date',false,true));
      content+=addProperty('Modification date','The date of the last modification',response.modificationDate,editable,buildInputOptions('set_modification_date','date',false,true));
    }
    // end of main column
    if(useForm){
      content+='<button type="submit" id="btn_submit_set_'+id+'" class="btn btn-primary mb-2">Submit</button>';
      content+='<button id="btn_cancel_set_'+id+'" class="btn btn-primary mb-2" onclick="$(\'#'+viewId+'\').hide();$(\'#'+viewId+'\').html(\'\');">Cancel</button>';
      content+='</form>';
    }
    content+='</div>';
    view.html(content);
    view.show();
    addClearCustomValidityHandler('set_form');
  }
  /* build the setting using the form data */
  /* id: the identifier of the entity or null */
  _formData(id){
    var json={};
    json.name=$('#set_name').val();
    json.builtin=$('#set_builtin').val();
    json.readOnly=$('#set_readOnly').val();
    json.type=$('#set_type').val();
    json.value=$('#set_value').val();
    // console.log("Data: " + JSON.stringify(json));
    return json;
  }
}
const settingController=new SettingController();