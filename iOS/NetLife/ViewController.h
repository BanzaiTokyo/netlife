//
//  ViewController.h
//  NetLife
//

//  Copyright (c) 2013 Toxa. All rights reserved.
//

#import <UIKit/UIKit.h>
#import <SpriteKit/SpriteKit.h>
#import "SocketRocket/SRWebSocket.h"
#pragma GCC diagnostic ignored "-Wundeclared-selector"
#import "MyScene.h"

@interface ViewController : UIViewController <UIAlertViewDelegate, SRWebSocketDelegate>
@property (nonatomic, weak) MyScene *scene;
-(void)sendMessage:(NSString *)message;
@end


@interface SettingsViewController : UIViewController <UIPickerViewDataSource, UIPickerViewDelegate>
@property (nonatomic, weak) ViewController *parent;
@property (nonatomic, strong) IBOutlet UIPickerView *colorPicker;
@end

