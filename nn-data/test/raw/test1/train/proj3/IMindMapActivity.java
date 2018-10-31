package com.src.main;

import com.src.view.MapView;
import com.srec.constain.paintConstain.SHAP;

import android.R.integer;
import android.app.Activity;
import android.content.Intent;
import android.os.Bundle;
import android.util.Log;
import android.view.Menu;
import android.view.MenuItem;
import android.view.View;
import android.view.View.OnClickListener;
import android.widget.ImageView;
import android.widget.LinearLayout;
import android.widget.TextView;

public class IMindMapActivity extends Activity implements OnClickListener{
	
	public static String TAG="midmap";
	
	private int groupId = 1;
	private int helpId = Menu.FIRST;
	private int aboutId = Menu.FIRST+1;
	private int exitId = Menu.FIRST+2;
	private MapView myMapView=null;
	private LinearLayout mapViewLayout=null;
	
    /** Called when the activity is first created. */
    @Override
    public void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.main);
        init();
    }
    
    private void init() {
    	initlayout();
		initMapview();
	}
    
    private void initlayout() {
		mapViewLayout=(LinearLayout)findViewById(R.id.mapViewLayout);
	}
    private void initMapview() {
		myMapView=new MapView(this);
		mapViewLayout.addView(myMapView);
		Log.d(TAG, "initmap");
	}
//    public void onclick_Event(View view){
//        	TextView textview = (TextView)findViewById(R.id.textview1);
//            textview.setText("Äãµã»÷ÁËButton");
//        }
    
    public boolean onCreateOptionsMenu(Menu menu) {
    	// TODO Auto-generated method stub
    	menu.add(groupId, helpId, helpId, null).setIcon(R.drawable.help);
    	menu.add(groupId, aboutId, aboutId, null).setIcon(R.drawable.about);
    	menu.add(groupId, exitId, exitId, null).setIcon(R.drawable.exit);
    	return super.onCreateOptionsMenu(menu);
    }
    
    @Override
    public boolean onOptionsItemSelected(MenuItem item) {
    	// TODO Auto-generated method stub
    	switch (item.getItemId()) {
		case 1:
			Intent helpIntent = new Intent(this, Help.class);
			this.startActivity(helpIntent);
			break;
		case 2:
			Intent aboutIntent = new Intent(this, About.class);
			this.startActivity(aboutIntent);
			break;
		case 3:
			finish();
		default:
			finish();
		}
    	return super.onOptionsItemSelected(item);
    }

	@Override
	public void onClick(View v) {
		// TODO Auto-generated method stub
		switch (v.getId()) {
		case R.id.diamond:
			myMapView.setChangeShape(SHAP.diamond);
			break;
		case R.id.line:
			myMapView.setChangeShape(SHAP.LINE);
			break;
		case R.id.oval:
			myMapView.setChangeShape(SHAP.OVAL);
			break;
		case R.id.rectangle:
			myMapView.setChangeShape(SHAP.RECT);
			break;
		case R.id.round:
			myMapView.setChangeShape(SHAP.CIRCLE);
			break;
		default:
			break;
		}
	}
    
    
}