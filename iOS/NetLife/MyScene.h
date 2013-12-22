//
//  MyScene.h
//  NetLife
//

//  Copyright (c) 2013 Toxa. All rights reserved.
//

#import <SpriteKit/SpriteKit.h>

extern const NSInteger maxLife;

@interface Player : SKNode
@property (nonatomic, strong) NSString *playerID;
@property (nonatomic) NSUInteger color;
@property (nonatomic, strong) NSMutableDictionary *cells;
@end

@interface Cell : SKShapeNode
@property (nonatomic, weak) Player *player;
@property (nonatomic) NSInteger life;
@property (nonatomic) NSInteger gridX;
@property (nonatomic) NSInteger gridY;
@end

@interface MyScene : SKScene
@property (nonatomic) BOOL active;
@property (nonatomic, strong) NSString *playerID;
@property (nonatomic) NSUInteger color;
@property (nonatomic, strong) NSMutableDictionary *players;
@property (nonatomic, strong) NSMutableDictionary *attackers;
@property (nonatomic, strong) NSMutableDictionary *taps;
@property (nonatomic, strong) SKNode *mainLayer;
-(void)abortGame;
-(void)addCell:(Cell *)cell :(NSString *)key;
-(void)removePlayer:(NSString *)playerID;
-(void)checkAttackerAtPos:(NSString *)key :(NSInteger)gridX :(NSInteger)gridY;
-(void)waitMode:(BOOL)wait;
@end
