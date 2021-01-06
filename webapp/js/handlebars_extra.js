Handlebars.registerHelper('registerPartial',(name,options) => Handlebars.registerPartial(name, options.fn));
Handlebars.registerHelper('ifNotEmpty',function(v,options){
  if(v==null||typeof v=='undefined'||v=='null'){
    return options.inverse(this);
  }
  return v.length==0?options.inverse(this):options.fn(this);
});
Handlebars.registerHelper('ifEquals',function(a,b,options){
  if(a===b){
    return options.fn(this);
  }
  return options.inverse(this);
});
Handlebars.registerHelper('default',function(v,d,options){
  if(v==null||typeof v=='undefined'||v=='null'){
    return d;
  }
  return v;
});
Handlebars.registerHelper('ifIsZero',function(v,options){
  if(v==null||typeof v=='undefined'||v=='null'){
    return options.fn(this);
  }
  if(v===0){
    return options.fn(this);
  }
  return options.inverse(this);
});
Handlebars.registerHelper('ifIsNotZero',function(v,options){
  if(v==null||typeof v=='undefined'||v=='null'){
    return options.inverse(this);
  }
  if(v===0){
    return options.inverse(this);
  }
  return options.fn(this);
});