#!/usr/bin/env python
import sys, string, bz2, re

class CivMap:
    def __init__(self, filename):
        self.filename = filename
        fp = open(filename)
        self.raw_map = string.split(bz2.decompress(fp.read()), "\n")

        self.geomap=[]
        self.map_i = 0

        while not self.raw_map[self.map_i].startswith("version"):
            self.map_i += 1
        version = int(self.raw_map[self.map_i].split("=")[1][0])

        #skip before map
        while self.raw_map[self.map_i][:2]!="t0":
            self.map_i = self.map_i + 1

        #get map
        while self.raw_map[self.map_i][:2] in ("t0", "t1"):
            #print self.raw_map[self.map_i]
            if version==2:
                self.geomap.append(self.raw_map[self.map_i][6:-1])
            else:
                self.geomap.append(self.raw_map[self.map_i][7:-1])
            self.map_i = self.map_i + 1

        while self.raw_map[self.map_i].find("nplayers") < 0:
            self.map_i = self.map_i + 1
        self.player_count = int(self.raw_map[self.map_i].split("=")[1])

        self.player_pos = []
        for count in range(self.player_count):
            self.get_player(self.player_pos)

        self.analyse_map()
        self.raw_map = None #not needed anymore

    def analyse_map(self):
        #print_geomap()
        self.usable_size = 0
        continent_count = 1
        players2analyse = self.player_pos[:]
        self.continent_stat_lst = []
        while players2analyse:
            pos = players2analyse[0]
            size, bad_size = self.color_map(pos[0], pos[1])
            continent_player_count = 0
            players2analyse_next = []
            for pos in players2analyse:
                if self.geomap[pos[1]][pos[0]]=="!":
                    continent_player_count += 1
                else:
                    players2analyse_next.append(pos)
            players2analyse = players2analyse_next
            self.continent_stat_lst.append((size, bad_size, continent_player_count))
            continent_count += 1
            self.usable_size += size

        self.outside_count, self.glacier_count = self.count_area_outside()
        self.usable_size += self.outside_count

    def get_player(self, pos_list):
        #get starting unit place
        while self.raw_map[self.map_i][:3]!="u={":
            self.map_i = self.map_i + 1
        self.map_i = self.map_i + 1
        attrs = string.split(self.raw_map[self.map_i], ",")
        pos_list.append(map(int, attrs[1:3]))

    def print_geomap(self):
        for s in self.geomap:
            print s

    def color_map(self, x, y):
        size = 0
        bad_size = 0
        lst = [(x, y)]
        while lst:
            x,y = lst.pop()
            y = y % len(self.geomap)
            x = x % len(self.geomap[0])
            if self.geomap[y][x] not in " !:":
                if self.geomap[y][x] in "dmt":
                    bad_size += 1
                self.geomap[y] = self.geomap[y][:x] + "!" + self.geomap[y][x+1:]
                size += 1
                lst.append((x-1, y-1))
                lst.append((x-1, y  ))
                lst.append((x-1, y+1))
                lst.append((x  , y+1))
                lst.append((x+1, y+1))
                lst.append((x+1, y  ))
                lst.append((x+1, y-1))
                lst.append((x  , y-1))
        return size, bad_size

    def get_coast_distance(self, x, y):
        i = 1
        while True:
            for j in range(-i, i+1):
                for x2, y2 in ((x+j, y-i),
                               (x+j, y+i),
                               (x-i, y+j),
                               (x+j, y+j)):
                    y2 = y2 % len(self.geomap)
                    x2 = x2 % len(self.geomap[0])
                    if self.geomap[y2][x2] in " :":
                        return i
            i += 1

    def count_area_outside(self):
        count = 0
        count_glacier = 0
        for line in self.geomap:
            for ch in line:
                if ch not in " !:":
                    if ch=="a":
                        count_glacier += 1
                    else:
                        count += 1
        return count, count_glacier

    def print_detailed(self):
        print "nplayers:", self.player_count
        for i in range(self.player_count):
            pos = self.player_pos[i]
            print "player", i, "coast distance:", self.get_coast_distance(pos[0], pos[1])
        continent_count = 1
        print "bad area is defined as desert, mountain or tundra"
        for size, bad_size, continent_player_count in self.continent_stat_lst:
            print "continent %i size: %i (without bad: %i), players: %i, size/player: %.1f (without bad %.1f)" % (continent_count, size, size-bad_size, continent_player_count, size/float(continent_player_count), (size-bad_size)/float(continent_player_count))
            continent_count += 1
        print "area outside: %i, size/player: %.1f, glacier: %i" % (self.outside_count, self.outside_count/float(self.player_count), self.glacier_count)
        print "world usable size: %i, world usable size/player: %.1f" % (self.usable_size, self.usable_size/float(self.player_count),)

    def print_header(self, continent_count):
        print "general format: size(without bad)/player_count=size_per_player(without bad)"
        print "bad area is defined as desert, mountain or tundra"
        print "world usable   outside glacier ",
        for i in range(continent_count):
            print "continent%i                " % (i+1,),
        print "filename"

    def print_short(self, max_continent_count):
        print "%5i/%3i=%3.0f " % (self.usable_size, self.player_count, self.usable_size/float(self.player_count),),
        print "%4i/=%3.0f  %4i " % (self.outside_count, self.outside_count/float(self.player_count), self.glacier_count),
        for size, bad_size, continent_player_count in self.continent_stat_lst:
            print "%5i(%5i)/%3i=%3.0f(%3.0f) " % (size, size-bad_size, continent_player_count, size/float(continent_player_count), (size-bad_size)/float(continent_player_count)),
        for i in range(max_continent_count - len(self.continent_stat_lst)):
            print " "*(5+2+5+1+3+1+3+2+3+1),
        print self.filename

if __name__=="__main__":
    if len(sys.argv) < 2:
        print "Usage: %s savefile1 [savefile2 savefile3...]"
        sys.exit(1)
    mode_single = len(sys.argv)==2
    if mode_single:
        civ_map = CivMap(sys.argv[1])
        civ_map.print_detailed()
    else:
        civ_map_lst = [CivMap(filename) for filename in sys.argv[1:]]
        max_continent_count = max([len(civ_map.continent_stat_lst) for civ_map in civ_map_lst])
        civ_map_lst[0].print_header(max_continent_count)
        for civ_map in civ_map_lst:
            civ_map.print_short(max_continent_count)
    
