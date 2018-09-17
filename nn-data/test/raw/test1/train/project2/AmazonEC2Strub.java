package com.siteview.realoracle.control;

import java.text.MessageFormat;

import javafx.animation.FillTransition;
import javafx.animation.FillTransitionBuilder;
import javafx.animation.Timeline;
import javafx.beans.property.SimpleStringProperty;
import javafx.beans.property.StringProperty;
import javafx.event.EventHandler;
import javafx.scene.Cursor;
import javafx.scene.Group;
import javafx.scene.control.Label;
import javafx.scene.control.Tooltip;
import javafx.scene.image.Image;
import javafx.scene.image.ImageView;
import javafx.scene.input.MouseEvent;
import javafx.scene.layout.HBox;
import javafx.scene.layout.Pane;
import javafx.scene.paint.Color;
import javafx.scene.shape.Rectangle;
import javafx.scene.text.Text;
import javafx.util.Duration;

import com.siteview.realoracle.PanelMap;
import com.siteview.realoracle.tools.AppGlobalString;
import com.siteview.realoracle.tools.BrowserUtil;
import com.siteview.realoracle.tools.ZHAndEN2TabManager;

public class PanelToolbar extends Pane {
	
	public static StringProperty dbLink = new SimpleStringProperty("链接数据库（\"db/hostname\"）");
	
	public static void setDbLinkName(String db,String hostName){
		String value = MessageFormat.format("链接数据库（\"{0}/{1}\"）",db,hostName);
		dbLink.setValue(value);
	}
	
	private PanelMap panelMap;
	public PanelToolbar(PanelMap pm) {
		panelMap = pm;
		loadUI();
	}

	public void loadUI() {
		
		this.prefWidthProperty().bind(AppGlobalString.width);
		
		HBox labHBox = new HBox();
		labHBox.setSpacing(10);

		Group connectLab =addLabel(dbLink,"Connect","connect");
		labHBox.getChildren().add(connectLab);

		Group switchLab = addLabel(ZHAndEN2TabManager.settingTitle, "Chinese and English switch","switch");
		labHBox.getChildren().add(switchLab);
		
//		Group historyLab =addLabel(new SimpleStringProperty("历史数据回放"),"History","history");
//		labHBox.getChildren().add(historyLab);
			
		labHBox.setTranslateX(0);
		labHBox.setTranslateY(5);
		
		errorLab = new Text();
		errorLab.setText("Connect Error ...			　");
		fillTransition = FillTransitionBuilder.create()
	            .duration(Duration.seconds(3))
	            .shape(errorLab)
	            .fromValue(Color.RED)
	            .toValue(Color.DODGERBLUE)
	            .cycleCount(Timeline.INDEFINITE)
	            .autoReverse(true)
	            .build();
		
		errorLab.setVisible(false);

		errorLab.setTranslateX(350);
		errorLab.setTranslateY(20);

		HBox group = addLink();
		group.setTranslateX(640);
		group.setTranslateY(5);

		
		this.getChildren().addAll(labHBox,errorLab,group);
	}

	public Group addLabelImage(StringProperty tile, String groupName,
			String imageName) {
		Group group = new Group();
		Label lab = new Label();
		Tooltip tip = new Tooltip();
		tip.textProperty().bind(tile);
		Tooltip.install(lab, tip);
		lab.setGraphic(addImage(imageName));
		lab.setOnMouseClicked(clickedEvent(tile, groupName));

		Rectangle selectStyle = new Rectangle();
		selectStyle.setFill(Color.TRANSPARENT);
		selectStyle.setStroke(Color.TRANSPARENT);
		selectStyle.widthProperty().bind(lab.widthProperty().add(2));
		selectStyle.heightProperty().bind(lab.heightProperty().add(2));
		selectStyle.setLayoutX(lab.getLayoutX() - 1);
		selectStyle.setLayoutY(lab.getLayoutY() - 1);
		selectStyle.setStrokeWidth(1.5);
		group.getChildren().addAll(selectStyle, lab);

		lab.setOnMouseEntered(mouseEvent(selectStyle, "Entered"));
		lab.setOnMouseExited(mouseEvent(selectStyle, "Exited"));
		return group;
	}

	public ImageView addImage(String imageUrl) {
		ImageView imageView = new ImageView();
		Image image = new Image("file:/"+System.getProperty("user.dir")+"/images/"+ imageUrl);
		imageView.setImage(image);
		imageView.setFitHeight(15);
		imageView.setFitWidth(15);
		return imageView;
	}

	private static int clickCount = 1;
	private static FillTransition fillTransition;
	private static Text errorLab;
	
	public static void showError(){
		if(errorLab.visibleProperty().getValue() == false){
			errorLab.setVisible(true);
			fillTransition.play();
		}
	}
	
	public static void closeError(){
		if(errorLab.visibleProperty().getValue() == true){
			errorLab.setVisible(false);
			fillTransition.pause();
		}
	}

	public EventHandler clickedEvent(final StringProperty titleName,final String groupName) {
		return new EventHandler<MouseEvent>() {
					@Override
					public void handle(MouseEvent t) {
						if (groupName.equals("serviceNode")) {
							
						}
						else if (groupName.equals("connect")) {
							Window.addNode(new OracleSetup(panelMap));
						} 
						else if (groupName.equals("history")) {
							new HistoryPlayPanel(panelMap.mainstate);
						} 
						else if (groupName.equals("tablespace")) {

						} 
						else if (groupName.equals("switch")) {
							
							if (ZHAndEN2TabManager.ZH_EN_TAB.getValue()
									.equals("EN")) {
								ZHAndEN2TabManager.ZH_EN_TAB.setValue("ZH");
							}
							else {
								ZHAndEN2TabManager.ZH_EN_TAB.setValue("EN");
							}
	
						
						} 
						else {

						}
					}
			};
	}

	public static EventHandler mouseEvent(final Rectangle selectStyle,
			final String eventName) {
		return new EventHandler<MouseEvent>() {
			@Override
			public void handle(MouseEvent t) {
				// Label lab = (Label) t.getSource();
				if (eventName.equals("Entered")) {// 获得焦点时触发
					selectStyle.setStroke(Color.WHITE);
				} else if (eventName.equals("Exited")) {// 离开焦点时触发
					selectStyle.setStroke(Color.TRANSPARENT);
				}
			}
		};
	}

	/** 判断是否连接数据库 **/
	public static boolean isLogin(String alertMsg) {
		if (AppGlobalString.currenConnectMap.isEmpty()) {
//			new Alert("info", alertMsg);
			return false;
		} else {
			return true;
		}

	}

	public Group addLabel(StringProperty tile, String tipTxt, String groupName) {
		Group group = new Group();
		Label lab = new Label();
		lab.setTextFill(Color.WHITE);
		lab.textProperty().bind(tile);
		Tooltip tip = new Tooltip();
		tip.setText(tipTxt);
		Tooltip.install(lab, tip);
		lab.setOnMouseClicked(clickedEvent(tile, groupName));

		Rectangle selectStyle = new Rectangle();
		selectStyle.setFill(Color.TRANSPARENT);
		//selectStyle.setStroke(Color.TRANSPARENT);
		selectStyle.setStroke(Color.WHITE);
		selectStyle.widthProperty().bind(lab.widthProperty().add(2));
		selectStyle.heightProperty().bind(lab.heightProperty().add(2));
		selectStyle.setLayoutX(lab.getLayoutX() - 1);
		selectStyle.setLayoutY(lab.getLayoutY() - 1);
		selectStyle.setStrokeWidth(1.5);
		group.getChildren().addAll(selectStyle, lab);

		//lab.setOnMouseEntered(mouseEvent(selectStyle, "Entered"));
		//lab.setOnMouseExited(mouseEvent(selectStyle, "Exited"));
		return group;
	}
	
	public HBox addLink(){
		HBox group = new HBox(8);
		Label moreLable = new Label();
		moreLable.setTextFill(Color.WHITE);
		moreLable.setText("更多的运维工具，请访问:");
		moreLable.setTranslateY(2);
	
		Text moreLink = new Text("www.siteview.com");
		moreLink.setCursor(Cursor.HAND);
		moreLink.fillProperty().setValue(Color.web("#48AE48"));
		moreLink.setUnderline(true);
		moreLink.setTranslateY(2.5);
		
		
		moreLink.setOnMouseClicked(new EventHandler<MouseEvent>() {
			@Override
			public void handle(MouseEvent event) {
				BrowserUtil.browse("http://www.siteview.com/?leadsrc=oraclepanel");
			}
		});
		
		Text weiboLink = new Text("关注微博");
		weiboLink.fillProperty().setValue(Color.web("#48AE48"));
		weiboLink.setCursor(Cursor.HAND);
		weiboLink.setUnderline(true);
		weiboLink.setTranslateY(2.5);
		
		weiboLink.setOnMouseClicked(new EventHandler<MouseEvent>() {
			@Override
			public void handle(MouseEvent event) {
				BrowserUtil.browse("http://weibo.com/siteview");
			}
		});
		
		Text bbsLink = new Text("论坛");
		bbsLink.setCursor(Cursor.HAND);
		bbsLink.fillProperty().setValue(Color.web("#48AE48"));
		bbsLink.setUnderline(true);
		bbsLink.setTranslateY(2.5);
		
		bbsLink.setOnMouseClicked(new EventHandler<MouseEvent>() {
			@Override
			public void handle(MouseEvent event) {
				BrowserUtil.browse("http://www.siteview.com/bbs/");
			}
		});

		group.getChildren().addAll(moreLable,moreLink,weiboLink,bbsLink);
		return group;
	}
}