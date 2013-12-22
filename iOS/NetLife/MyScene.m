//
//  MyScene.m
//  NetLife
//
//  Created by Toxa on 06/12/13.
//  Copyright (c) 2013 Toxa. All rights reserved.
//

#import "MyScene.h"
#import "ViewController.h"

const NSInteger gridW = 7;
const NSInteger gridH = 12;
const NSInteger maxLife = 30;
CGSize cellSize;
SKShapeNode *grid;
NSInteger maxMyCells = 0;

@implementation Player
@end

@implementation Cell
-(id)init {
    if (self = [super init]) {
        CGMutablePathRef path = CGPathCreateMutable();
        CGRect r = CGRectMake(0, 0, cellSize.width, cellSize.height);
        r = CGRectInset(r, self.lineWidth*2, self.lineWidth*2);
        CGPathAddRect(path, NULL, r);
        self.path = path;
        self.player = nil;
        self.life = maxLife;
    }
    return self;
}
-(void)setLife:(NSInteger)life {
    _life = life;
    self.fillColor = [UIColor colorWithRed:self.player.color & 0xFF0000 green:self.player.color & 0x00FF00 blue:self.player.color & 0x0000FF alpha:life/(float)maxLife];
    self.strokeColor = [UIColor colorWithRed:self.player.color & 0xFF0000 green:self.player.color & 0x00FF00 blue:self.player.color & 0x0000FF alpha:1];
}

@end

SKLabelNode *myLabel;
@implementation MyScene

-(id)initWithSize:(CGSize)size {
    if (self = [super initWithSize:size]) {
        self.backgroundColor = [SKColor colorWithRed:0.15 green:0.15 blue:0.3 alpha:1.0];
        self.mainLayer = [SKNode node];
        [self addChild:self.mainLayer];
        
        myLabel = [SKLabelNode labelNodeWithFontNamed:@"Chalkduster"];
        myLabel.text = @"Hello, World!";
        myLabel.fontSize = 10;
        myLabel.position = CGPointMake(CGRectGetMidX(self.frame), self.frame.size.height*0.9);
        
        [self addChild:myLabel];
        
        grid = [SKShapeNode node];
        CGMutablePathRef path = CGPathCreateMutable();
        NSInteger maxSize = MAX(self.frame.size.width, self.frame.size.height);
        NSInteger minSize = MIN(self.frame.size.width, self.frame.size.height);
        minSize = MIN(minSize / (float)gridW, minSize / (float)gridH);
        cellSize = CGSizeMake(minSize, minSize);
        cellSize = CGSizeMake(self.frame.size.width/(float)gridW, self.frame.size.height/(float)gridH);
        float x = 0, y = 0;
        while (x < maxSize) {
            CGPathMoveToPoint(path, NULL, x, 0);
            CGPathAddLineToPoint(path, NULL, x, maxSize);
            x += cellSize.width;
        }
        while (y < maxSize) {
            CGPathMoveToPoint(path, NULL, 0, y);
            CGPathAddLineToPoint(path, NULL, maxSize, y);
            y += cellSize.height;
        }
        grid.path = path;
        grid.strokeColor = [UIColor colorWithRed:0.5 green:0.5 blue:0.5 alpha:1.0];
        //grid.lineWidth = 1;
        grid.antialiased = NO;
        [self addChild:grid];
        self.active = NO;
    }
    return self;
}

-(void)abortGame {
    [NSObject cancelPreviousPerformRequestsWithTarget:self];
    [self.mainLayer removeAllChildren];
    self.attackers = [NSMutableDictionary dictionary];
    self.taps = [NSMutableDictionary dictionary];
    self.active = NO;
}

-(void)checkAttackerAtPos:(NSString *)key :(NSInteger)gridX :(NSInteger)gridY {
    if (self.attackers[key]) return;
    CGPoint pt = CGPointMake((gridX + 0.5) * cellSize.width, (gridY + 0.5) * cellSize.height);
    BOOL hasOwn = NO, hasOther = NO;
    for (Cell *c in [self.mainLayer nodesAtPoint:pt])
        if ([c isKindOfClass:[Cell class]]) {
            hasOwn = hasOwn || [c.player.playerID isEqualToString:self.playerID];
            hasOther = hasOther || ![c.player.playerID isEqualToString:self.playerID];
        }
    if (hasOwn && hasOther) {
        SKLabelNode *attacked = [SKLabelNode labelNodeWithFontNamed:@"Chalkduster"];
        attacked.text = @"*";
        attacked.fontSize = 20;
        attacked.position = CGPointMake(pt.x+1, pt.y-3);
        attacked.zPosition = maxLife + 1;
        [attacked runAction:[SKAction repeatActionForever:[SKAction sequence:@[[SKAction fadeOutWithDuration:0.1], [SKAction waitForDuration:0.5], [SKAction fadeInWithDuration:0.1], [SKAction waitForDuration:0.5]]]]];
        [self.mainLayer addChild:attacked];
        self.attackers[key] = attacked;
    }
}

-(void)addCell:(Cell *)cell :(NSString *)key {
    cell.position = CGPointMake(cell.gridX * cellSize.width, cell.gridY * cellSize.height);
    [self.mainLayer addChild:cell];
    [self checkAttackerAtPos:key :cell.gridX :cell.gridY];
}

-(void)removePlayer:(NSString *)playerID {
    if (self.players[playerID])
        for (Cell *cell in ((Player *)self.players[playerID]).cells.allValues)
            [cell removeFromParent];
    [self.players removeObjectForKey:playerID];
    if ([playerID isEqualToString: self.playerID]) {
        self.active = NO;
        [NSObject cancelPreviousPerformRequestsWithTarget:self];
        [(ViewController *)((UIView *)self.view).window.rootViewController sendMessage:@"{\"code\":2}"];
    }
}

-(void)touchesEnded:(NSSet *)touches withEvent:(UIEvent *)event {
    [super touchesEnded:touches withEvent:event];
    if (!self.active) return;
    /* Called when a touch begins */
    UITouch *touch = [touches anyObject];
    CGPoint location = [touch locationInNode:self];
    NSInteger cellX = floor(location.x / cellSize.width);
    NSInteger cellY = floor(location.y / cellSize.height);
    location = CGPointMake(cellX * cellSize.width, cellY * cellSize.height);
    NSArray *check = [self.mainLayer nodesAtPoint:location];
    for (SKNode *n in check)
        if ([n isKindOfClass:[Cell class]]) {
            Cell *c = (Cell *)n;
            if ([c.player.playerID isEqualToString: self.playerID] && c.life < maxLife) { //tapped on an own cell
                c.zPosition =  ++c.life;
                NSString *key = [NSString stringWithFormat:@"%d %d", c.gridX, c.gridY];
                [self checkAttackerAtPos:key :c.gridX :c.gridY];
                self.taps[key] = [NSNumber numberWithInteger:c.life];
                return;
            }
        }
    
    for (int x=-1; x<2; x++)
        for (int y=-1; y<2; y++) {
            if (!x && !y) continue;
            NSString *key = [NSString stringWithFormat:@"%d %d", (cellX + x), (cellY + y)];
            Player *p = (Player *)self.players[self.playerID];
            if (!p.cells[key]) continue;
            //found a neighbour own cell, OK to place a new on tapped coordinates
            Cell *c = [Cell node];
            c.player = p;
            c.zPosition = c.life = maxLife/2;
            c.gridX = cellX;  c.gridY = cellY;
            key = [NSString stringWithFormat:@"%d %d", cellX, cellY];
            p.cells[key] = c;
            [self addCell:c :key];
            self.taps[key] = [NSNumber numberWithInteger:c.life];
            return;
        }
}

-(void)sendTap:(Cell *)c {
    NSString *msg = [NSString stringWithFormat:@"{\"code\":3, \"tap\":\"%d %d\"}", c.gridX, c.gridY];
    [(ViewController *)((UIView *)self.view).window.rootViewController sendMessage:msg];
}

-(void)waitMode:(BOOL)wait {
    maxMyCells = 0;
    for (Cell *c in [((Player *)self.players[self.playerID]).cells allValues])
        maxMyCells = MAX(maxMyCells, c.life);
    if (wait) {
        self.userInteractionEnabled = NO;
        self.active = NO;
        myLabel.text = @"Waiting for other players...";
        if (maxMyCells != 1)
            return;
        [self abortGame];
        myLabel.text = @"Game over";
        self.active = NO;
        UIAlertView *alert = [NSClassFromString(@"_UIAlertManager") performSelector:@selector(topMostAlert)];
        if (!alert) {
            alert = [[UIAlertView alloc] initWithTitle:@"Game Over" message:@"Play again?" delegate:((UIView *)self.view).window.rootViewController cancelButtonTitle:@"NO" otherButtonTitles:@"YES", nil];
            [alert show];
        }
    }
    else {
        self.userInteractionEnabled = YES;
        self.active = self.players[self.playerID] != nil;
        self.taps = [NSMutableDictionary dictionary];
        if (maxMyCells)
            myLabel.text = [NSString stringWithFormat:@"Last cell dies in %d steps", maxMyCells];
        else
            myLabel.text = @"";
        //[self performSelector:@selector(tickAction) withObject:nil afterDelay:1.0];
    }
}
-(void)update:(CFTimeInterval)currentTime {
    /* Called before each frame is rendered */
}

@end
