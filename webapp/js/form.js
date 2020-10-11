function contains(text,needle){
  if(isValid(text) && isValid(needle)){
    return text.indexOf(needle)!==-1;
  }
  return false;
}
function clearCustomValidity(formId){
  $('#'+formId+' :input').each(function(){
    $(this)[0].setCustomValidity('');
  });
}
function addClearCustomValidityHandler(formId){
  $('#'+formId+' :input').each(function(){
    $(this).on('input',function(){
      $(this)[0].setCustomValidity('');
    });
  });
}
function handleValidationError(prefix,x){
  var message=undefined;
  if(isValid(x.status)&&x.status==200){
    return;
  }
  if(isValid(x.responseText)){
    message=x.responseText.trim();
    if(message.startsWith(':')){
      message=message.substring(1);
    }
  }
  if(x.status==400 && isValid(x.responseText)){
    console.log(x.responseText);
    var show=true;
    var parts=x.responseText.split(':');
    if(parts.length>1){
      // console.log(parts[0]);
      // console.log(capitalizeFirst(parts[1]));
      const input=$('#'+prefix+'_'+parts[0])[0];
      if(isValid(input)){
        input.setCustomValidity(capitalizeFirst(parts[1]));
        const form=$('#'+prefix+'_form')[0];
        if(isValid(form)){
          form.reportValidity();
          show=false
        }
      }
    }
    if(show){
      showError('Message: '+message);
    }
  }else if(isValid(message)){
    showError($.i18n('error_code')+': '+x.status+'<br/>'+$.i18n('message')+': '+message);
  }else{
    showError($.i18n('error_code')+': '+x.status);
  }
}
function capitalizeFirst(text){
  return text.charAt(0).toUpperCase()+text.slice(1);
}
function isNormalInteger(data){
  return /^\+?(0|[1-9]\d*)$/.test(data);
}
function isValid(data){
  return data!==null && typeof data!=='undefined' && data!=='null';
}
function isNotEmpty(data){
  return data!==null && typeof data!=='undefined' && data!=='null' && data!=='';
}
function addTableHeader(){
  var content='<div class="row row-header">';
  content+='<div class="column column-header col-lg-4 capitalized" data-i18n="name"></div>';
  content+='<div class="column column-header col-lg-8 capitalized" data-i18n="value"></div>';
  content+='</div>';
  return content;
}
function addTableRow(label,title,value){
  var content='<div class="row">';
  content+='<div class="column col-lg-4 capitalized" title="'+title+'">'+label+':</div>';
  content+='<div class="column col-lg-8">';
  if(isValid(value)){
    content+=value;
  }
  content+='</div>';
  content+='</div>';
  return content;
}
function addPropertiesHeader(){
  var content='<div class="row row-header">';
  content+='<div class="column column-header col-lg-4 capitalized" data-i18n="property"></div>';
  content+='<div class="column column-header col-lg-8 capitalized" data-i18n="value"></div>';
  content+='</div>';
  return content;
}
function buildSelectOption(value,label){
  var result={};
  result.value=value;
  result.label=label;
  return result;
}
function buildFileInputOptions(fieldId,accept,required,disabled){
  var result={};
  result.fieldId=fieldId;
  result.type='file';
  result.disabled=disabled;
  result.required=required;
  result.min=required ? 1 : 0;
  result.max=1024;
  result.accept=accept;
  return result;
}
function buildRemoteFileInputOptions(fieldId,accept,required,disabled){
  var result={};
  result.fieldId=fieldId;
  result.type='';
  result.disabled=disabled;
  result.required=required;
  result.min=required ? 1 : 0;
  result.max=1024;
  result.pattern='([A-Z-a-z0-9-_\\s\\/:\\\\])*';
  if (isValid(accept)) {
    result.pattern+=accept.replace('.','\\.');
  }
  return result;
}
function buildLogLevelInputOptions(fieldId,required,disabled){
  var options=buildInputOptions(fieldId,'select',required,disabled);
  options.items=[];
  options.items.push(buildSelectOption('DEBUG',$.i18n('debug')));
  options.items.push(buildSelectOption('INFO',$.i18n('information')));
  options.items.push(buildSelectOption('WARN',$.i18n('warning')));
  options.items.push(buildSelectOption('ERROR',$.i18n('error')));
  return options;
}
function buildThreadPriorityInputOptions(fieldId,required,disabled){
  var options=buildInputOptions(fieldId,'select',required,disabled);
  options.items=[];
  options.items.push(buildSelectOption('5',$.i18n('normal')));
  options.items.push(buildSelectOption('1',$.i18n('low')));
  options.items.push(buildSelectOption('10',$.i18n('high')));
  return options;
}
function buildInputOptions(fieldId,type,required,disabled,min,max){
  var result={};
  result.fieldId=fieldId;
  result.type=type;
  result.disabled=disabled;
  result.required=required;
  result.min=min;
  result.max=max;
  return result;
}
function buildBooleanInputOptions(fieldId,required,disabled){
  var options=buildInputOptions(fieldId,'select',required,disabled);
  options.items=[];
  options.items.push(buildSelectOption('false',$.i18n('no')));
  options.items.push(buildSelectOption('true',$.i18n('yes')));
  return options;
}
function capitalize(value){
  if (!isValid(value)){
    return value;
  }
  return value.charAt(0).toUpperCase()+value.slice(1);
}
function buildInput(title,value,options){
  var content='<';
  // console.log("title: "+title);
  // console.log("options: "+JSON.stringify(options));
  if(isValid(options.type)&&options.type=='boolean'){
    content+='input class="form-check-input" type="checkbox"';
    if (isValid(value)) {
      content+=value=='true'?' selected':'';
    }
  }else if(isValid(options.type)&&options.type=='select'){
    content+='select class="form-control"';
  }else{
    content+='input type="'+options.type+'" class="form-control" placeholder="'+title+'..."';
    if(isValid(options.accept)){
      content+=' accept="'+options.accept+'"';
    }
    if(isValid(options.pattern)){
      content+=' pattern="'+options.pattern+'"';
    }
    if(isValid(options.autocomplete)&&options.autocomplete){
      content+=' autocomplete="on"';
    }else{
      content+=' autocomplete="new-'+options.fieldId+'"';
    }
    if(isValid(options.min)&&options.min){
      if(isValid(options.type)&&options.type=='number'){
        content+=' min="'+options.min+'"';
        if (value < options.min) {
          value=options.min;
        }
      }else{
        content+=' minLength="'+options.min+'"';
      }
    }
    if(isValid(options.max)&&options.max){
      if(isValid(options.type)&&options.type=='number'){
        content+=' max="'+options.max+'"';
      }else{
        content+=' maxLength="'+options.max+'"';
      }
    }
    if(isValid(value)){
      content+=' value="'+value+'"';
    }
  }
  if(isValid(options.fieldId)&&options.fieldId){
    content+=' id="'+options.fieldId+'"';
  }
  if(isValid(options.disabled)&&options.disabled){
    content+=' disabled';
  }else if(isValid(options.required)&&options.required){
    content+=' required';
  }
  content+='>';
  if(isValid(options.type)&&options.type=='select'){
    if(isValid(options.items)&&options.items.length>0){
      const len=options.items.length;
      for(var i=0; i<len; i++){
        content+='<option value="'+options.items[i].value+'"';
        if (value===options.items[i].value||String(value)===String(options.items[i].value)) {
          content+=" selected";
        }
        content+=">"+capitalize(options.items[i].label)+"</option>";
      }
    }
    content+='</select>';
  }
  return content;
}