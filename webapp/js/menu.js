/* methods prefixed by '_' can be considered as private or protected (called by the other methods of the object or by html handler defined by this class */
class MenuController{
  /* constructor */
  constructor(){
    console.log('Initialization of MenuController...');
    console.log('MenuController initialized');
  }
  onClick(elt){
  	if(elt&&$(elt).hasClass('disabled')){
  	  return;
  	}
  	if(elt.id=='mni_detection_zone'){
      showContent('detection_zone');
    }else if(elt.id=='mni_detection_periods'){
	  showContent('detection_periods');
	}else if(elt.id=='mni_detection_filters'){
	  showContent('detection_filters');
	}else if(elt.id=='mni_status'){
	  showContent('status');
	}else if(elt.id=='mni_settings'){
	  showContent('settings');
	}else if(elt.id=='mni_help'){
	  showContent('help');
	}else if(elt.id=='mni_home'){
	  showContent('home');
	}
	this.update();
  }
  update(){
	const currentPage=Cookies.get('currentPage');
	var selected=null;
    if(currentPage=='detection_zone'){
      selected='mni_detection_zone';
    }else if(currentPage=='detection_periods'){
	  selected='mni_detection_periods';
	}else if(currentPage=='detection_filters'){
	  selected='mni_detection_filters';
	}else if(currentPage=='status'){
	  selected='mni_status';
	}else if(currentPage=='settings'){
	  selected='mni_settings';
	}else if(currentPage=='help'){
	  selected=null;
	}else{
	  selected='mni_home';
	}
	if(selected){
	  $('#menubar').find('.menu-item').each(function(){
	    if(this.id){
	      if(this.id===selected){
	        $(this).addClass('disabled');
	        $(this).removeClass('clickable');
	      }else{
	        $(this).removeClass('disabled');
	        $(this).addClass('clickable');
	      }
	    }
	  });
	}
  }
}
const menuController=new MenuController();