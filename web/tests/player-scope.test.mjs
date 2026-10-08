import {test} from 'node:test'
import assert from 'node:assert/strict'
import fs from 'node:fs'
import {leaderboardTeam,resolveTeam} from '../src/scope.ts'

const teams=JSON.parse(fs.readFileSync(new URL('../public/data/index.json',import.meta.url))).teams

test('main Player Stats defaults and invalid or removed aliases resolve to Blue',()=>{
 for(const requested of [null,'','not-a-team','removed-alias','blue'])
  assert.equal(leaderboardTeam(teams,requested).slug,'blue')
 assert.equal(leaderboardTeam(teams,'white').slug,'white')
})

test('shared team resolution honors canonical slugs and existing aliases',()=>{
 const renamed=teams.map(t=>({...t,aliases:t.slug==='white'?['silver']:t.aliases}))
 assert.equal(resolveTeam(renamed,'silver').slug,'white')
 assert.equal(leaderboardTeam(renamed,'silver').slug,'white')
 assert.equal(resolveTeam(renamed,'missing'),undefined)
})

test('generic published teams work; missing Blue defaults to first active team',()=>{
 const generic=[{slug:'gray',active:0,aliases:[]},{slug:'yellow',active:1,aliases:['gold']},{slug:'black',active:1,aliases:[]}]
 assert.equal(leaderboardTeam(generic,null).slug,'yellow')
 assert.equal(leaderboardTeam(generic,'black').slug,'black')
 assert.equal(leaderboardTeam(generic,'gold').slug,'yellow')
 assert.equal(leaderboardTeam([],null),undefined)
 assert.equal(leaderboardTeam([generic[0]],null),undefined)
 assert.equal(leaderboardTeam(teams,null).slug,'blue')
})

test('team season/career exports preserve map ownership and distinct scopes',()=>{
 const load=name=>JSON.parse(fs.readFileSync(new URL('../public/data/'+name,import.meta.url)))
 for(const period of ['fall-2026','career']){
  const blue=load(`teams/blue/${period}.json`),white=load(`teams/white/${period}.json`)
  assert.equal(blue.team.slug,'blue');assert.equal(white.team.slug,'white')
  assert.equal(blue.players.length,5);assert.equal(white.players.length,4)
  assert.equal(blue.sub_players.length,0);assert.equal(white.sub_players.length,1)
  assert.ok(blue.matches.every(m=>m.team_slug==='blue'))
  assert.ok(white.matches.every(m=>m.team_slug==='white'))
 }
 // Global Career profiles retain their separate cross-team source and splits.
 assert.equal(load('players/lgon/career.json').rounds,82)
 assert.equal(load('players/lgon/career.json').series_ratings.length,3)
})
