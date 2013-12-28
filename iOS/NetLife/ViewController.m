//
//  ViewController.m
//  NetLife
//
//  Created by Toxa on 06/12/13.
//  Copyright (c) 2013 Toxa. All rights reserved.
//

#import "ViewController.h"

@implementation ViewController {
SRWebSocket *_webSocket;
}

-(void)prepareForSegue:(UIStoryboardSegue *)segue sender:(id)sender {
    ((SettingsViewController *)segue.destinationViewController).parent = self;
}
- (IBAction)goSettings:(id)sender {
    if (self.scene.active) {
        UIAlertView *alert = [[UIAlertView alloc] initWithTitle:@"Escape game?" message:nil delegate:self cancelButtonTitle:@"NO" otherButtonTitles:@"YES", nil];
        alert.tag = 1;
        [alert show];
    }
    else if (_webSocket.readyState == SR_OPEN)
        [self performSegueWithIdentifier:@"settings" sender:nil];
    else if (_webSocket.readyState != SR_CONNECTING)
        [self webSocket:_webSocket didFailWithError:nil];
}

- (void)_reconnect;
{
    _webSocket.delegate = nil;
    [_webSocket close];
    
    _webSocket = [[SRWebSocket alloc] initWithURLRequest:[NSURLRequest requestWithURL:[NSURL URLWithString:@"ws://chattish.com:443/life"]]];
    _webSocket.delegate = self;
    
    self.title = @"Opening Connection...";
    [_webSocket open];
    
}

/*- (void)viewWillAppear:(BOOL)animated
{
    [super viewWillAppear:animated];
    [self _reconnect];
}

- (void)viewDidDisappear:(BOOL)animated
{
	[super viewDidDisappear:animated];
    
    _webSocket.delegate = nil;
    [_webSocket close];
    _webSocket = nil;
}*/

- (void)viewDidLoad
{
    [super viewDidLoad];

    [self _reconnect];
    
    // Configure the view.
    SKView * skView = (SKView *)self.view;
    skView.showsFPS = YES;
    skView.showsNodeCount = YES;
    
    // Create and configure the scene.
    self.scene = [MyScene sceneWithSize:skView.bounds.size];
    self.scene.scaleMode = SKSceneScaleModeAspectFill;
    self.scene.active = NO;
    
    // Present the scene.
    [skView presentScene:self.scene];
}

- (BOOL)shouldAutorotate
{
    return YES;
}

- (NSUInteger)supportedInterfaceOrientations
{
    if ([[UIDevice currentDevice] userInterfaceIdiom] == UIUserInterfaceIdiomPhone) {
        return UIInterfaceOrientationMaskAllButUpsideDown;
    } else {
        return UIInterfaceOrientationMaskAll;
    }
}

- (void)didReceiveMemoryWarning
{
    [super didReceiveMemoryWarning];
    // Release any cached data, images, etc that aren't in use.
}

- (void)alertView:(UIAlertView *)alertView clickedButtonAtIndex:(NSInteger)buttonIndex {
    if (alertView.tag == 1) { //game running, "settings tapped"
        if (buttonIndex == 1) {
            [self.scene removePlayer:self.scene.playerID];
            [self performSegueWithIdentifier:@"settings" sender:nil];
        }
    }
    else if (alertView.tag == 2) { //connection lost, reconnect?
        if (buttonIndex == 1) {
            [self _reconnect];
        }
    }
    else if (buttonIndex == 1) //game over, play again?
        [self joinGame];
}

#pragma mark - SRWebSocketDelegate

- (void)webSocketDidOpen:(SRWebSocket *)webSocket {
    NSLog(@"Websocket Connected");
    self.title = @"Connected!";
}

- (void)webSocket:(SRWebSocket *)webSocket didFailWithError:(NSError *)error {
    NSLog(@":( Websocket Failed With Error %@", error);
    
    self.title = @"Connection Failed! (see logs)";
    _webSocket = nil;
    [self.scene abortGame];
    UIAlertView *alert = [[UIAlertView alloc] initWithTitle:@"Connection Failed" message:@"Try again?" delegate:self cancelButtonTitle:@"NO" otherButtonTitles:@"YES", nil];
     alert.tag = 2;
     [alert show];
}

- (void)webSocket:(SRWebSocket *)webSocket didReceiveMessage:(id)message {
    NSLog(@"Received \"%@\"", message);
    NSDictionary *data = [NSJSONSerialization JSONObjectWithData:[message dataUsingEncoding:NSUTF8StringEncoding] options:0 error:nil];
    NSInteger code = [data[@"code"] intValue];
    switch (code) {
        case 2: // player exited // {"code":2, "playerID":playerID}
            if ([data[@"playerID"] isEqualToString:self.scene.playerID]) {
                [self.scene abortGame];
                self.scene.statusText.text = @"Game over";
                self.scene.active = NO;
                UIAlertView *alert = [NSClassFromString(@"_UIAlertManager") performSelector:@selector(topMostAlert)];
                if (!alert && !self.presentedViewController) {
                    alert = [[UIAlertView alloc] initWithTitle:@"Game Over" message:@"Play again?" delegate:((UIView *)self.view).window.rootViewController cancelButtonTitle:@"NO" otherButtonTitles:@"YES", nil];
                    [alert show];
                }
            }
            else
                [self.scene removePlayer:data[@"playerID"]];
            break;
        case 3: {// signal to send taps
            NSMutableArray *tapData = [NSMutableArray arrayWithCapacity:self.scene.taps.count];
            for (NSString *key in self.scene.taps)
                [tapData addObject:[NSString stringWithFormat:@"%@ %@", key, self.scene.taps[key]]];
            NSString *msg = [NSString stringWithFormat:@"{\"code\": 3, \"marker\": %@, \"data\": \"%@\"}", data[@"marker"], [tapData componentsJoinedByString:@" "]];
            [self sendMessage:msg];
            [self.scene waitMode:YES];
            break;
        }
        case 4:// current game state), // {"code":4, "players": ["id":playerID, "color":color, "cells": "gridX gridY life ...]}
            self.scene.players = [NSMutableDictionary dictionary];
            self.scene.attackers = [NSMutableDictionary dictionary];
            [self.scene.mainLayer removeAllChildren];
            for (NSDictionary *playerData in data[@"players"]) {
                Player *player = [Player node];
                player.playerID = playerData[@"playerID"];
                player.color = [playerData[@"color"] integerValue];
                self.scene.players[player.playerID] = player;
                NSArray *cellData = [playerData[@"cells"] componentsSeparatedByString:@" "];
                NSInteger count = cellData.count/3;
                player.cells = [NSMutableDictionary dictionaryWithCapacity:count];
                for (int i=0; i<count; i++) {
                    Cell *cell = [Cell node];
                    cell.player = player;
                    cell.gridX = [cellData[i*3] intValue];
                    cell.gridY = [cellData[i*3+1] intValue];
                    cell.zPosition = cell.life = [cellData[i*3+2] intValue];
                    NSString *key = [NSString stringWithFormat:@"%d %d", cell.gridX, cell.gridY];
                    player.cells[key] = cell;
                    [self.scene addCell:cell :key];
                }
            }
            [self.scene waitMode:NO];
            break;
    }
}

- (void)webSocket:(SRWebSocket *)webSocket didCloseWithCode:(NSInteger)code reason:(NSString *)reason wasClean:(BOOL)wasClean {
    NSLog(@"WebSocket closed");
    self.title = @"Connection Closed! (see logs)";
    _webSocket = nil;
    [self.scene abortGame];
    UIAlertView *alert = [NSClassFromString(@"_UIAlertManager") performSelector:@selector(topMostAlert)];
    if (alert)
        [alert dismissWithClickedButtonIndex:0 animated:NO];
    alert = [[UIAlertView alloc] initWithTitle:@"Connection Lost" message:@"Try again?" delegate:self cancelButtonTitle:@"NO" otherButtonTitles:@"YES", nil];
    alert.tag = 2;
    [alert show];
}

-(void)sendMessage:(NSString *)message {
    [_webSocket send:message];
}

-(void)joinGame {
    NSDictionary *joinData = @{
                               @"code": @"1",
                               @"playerID": self.scene.playerID,
                               @"color": [NSString stringWithFormat:@"%u", self.scene.color]
                               };
    NSData *d = [NSJSONSerialization dataWithJSONObject:joinData options:0 error:nil];
    NSString *s = [[NSString alloc] initWithData:d encoding:NSUTF8StringEncoding];
    [self sendMessage:s];
    [self dismissViewControllerAnimated:YES completion:nil];
    [self.scene waitMode:YES];
}
@end

@implementation SettingsViewController {
    NSArray *colors;
}
-(void)viewDidLoad {
    colors = @[[UIColor redColor], [UIColor orangeColor], [UIColor yellowColor], [UIColor greenColor], [UIColor cyanColor], [UIColor blueColor], [UIColor purpleColor]];
    [self.colorPicker selectRow:0 inComponent:0 animated:NO];
}
- (IBAction)goBack:(id)sender {
    [self dismissViewControllerAnimated:YES completion:nil];
}
- (NSInteger)numberOfComponentsInPickerView:(UIPickerView *)thePickerView {
    return 1;
}

- (NSInteger)pickerView:(UIPickerView *)thePickerView numberOfRowsInComponent:(NSInteger)component {
    return 7;
}

-(UIView *)pickerView:(UIPickerView *)pickerView viewForRow:(NSInteger)row forComponent:(NSInteger)component reusingView:(UIView *)view {
    UIView *v;
    v = [[UIView alloc] initWithFrame:CGRectMake(0.0f, 0.0f,
                                                 [pickerView rowSizeForComponent:component].width - 10.0f, [pickerView rowSizeForComponent:component].height)];
    v.backgroundColor = colors[row];
    return v;
}
-(void)pickerView:(UIPickerView *)pickerView didSelectRow:(NSInteger)row inComponent:(NSInteger)component {
    
}

- (IBAction)joinGame:(id)sender {
    CGFloat r, g, b;
    [colors[[self.colorPicker selectedRowInComponent:0]] getRed:&r green:&g blue:&b alpha:nil];
    self.parent.scene.color = (NSUInteger)(r*255+0.5) << 16 | (NSUInteger)(g*255+0.5) << 8 | (NSUInteger)(b*255+0.5);
    if (!self.parent.scene.playerID) {
        self.parent.scene.playerID = [UIDevice currentDevice].identifierForVendor.UUIDString;
    }
    [self.parent joinGame];
}
@end