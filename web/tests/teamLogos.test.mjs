import {test} from 'node:test'
import assert from 'node:assert/strict'
import {readFileSync} from 'node:fs'
import {createHash} from 'node:crypto'
import {PROGRAM_LOGO,TEAM_LOGOS,teamLogoAsset,teamLogoSources,availableTeamLogo} from '../src/teamLogos.ts'

for(const slug of ['blue','white','grey','black'])test(`${slug} resolves its authoritative supplied team logo`,()=>{
 assert.equal(teamLogoAsset(slug),`brand/teams/${slug}.png`)
 assert.equal(teamLogoAsset(' '+slug.toUpperCase()+' '),TEAM_LOGOS[slug])
 assert.deepEqual(teamLogoSources(slug),[`/brand/teams/${slug}.png`,`/${PROGRAM_LOGO}`])
})
test('unknown, missing and unsafe team names fall back to program branding without inventing a path',()=>{
 for(const slug of ['future-team','constructor','__proto__','../../private','https://example.com/logo',null,undefined,''])assert.deepEqual(teamLogoSources(slug),[`/${PROGRAM_LOGO}`])
 assert.deepEqual(teamLogoSources('white','/tracker/'),['/tracker/brand/teams/white.png','/tracker/'+PROGRAM_LOGO])
 assert.deepEqual(teamLogoSources('blue','/tracker'),teamLogoSources('blue','/tracker/'))
})
test('failed team images fall back once; failed program image ends safely without retry loops',()=>{
 const [primary,fallback]=teamLogoSources('blue')
 assert.equal(availableTeamLogo('blue',[]),primary)
 assert.equal(availableTeamLogo('blue',[primary]),fallback)
 assert.equal(availableTeamLogo('blue',[primary,fallback]),null)
 assert.equal(availableTeamLogo('white',[primary]),'/brand/teams/white.png')
 assert.equal(availableTeamLogo('future-team',[fallback]),null)
})
test('installed PNG bytes, alpha channel and proportions match supplied source assets',()=>{
 const hashes={blue:'f020f8f766a9ba228eadc95270a134ca6eb2cf4d4c7f23f25699e9013d299d1d',white:'982b74b87697e80a5879fc4a407582f2522513dad68145d0246027ca0b1c37b7',grey:'d51f9d615781978678a03ab0c5ab93b4875960e610f8173e1fc55ec6092256b3',black:'95a0e92fcf599501673874edc0ea3e6582cfe8466983335299fb69839cf055a7'}
 for(const [slug,hash] of Object.entries(hashes)){
  const data=readFileSync(new URL(`../public/brand/teams/${slug}.png`,import.meta.url))
  assert.equal(createHash('sha256').update(data).digest('hex'),hash)
  assert.equal(data.subarray(0,8).toString('hex'),'89504e470d0a1a0a')
  assert.equal(data.readUInt32BE(16),1080);assert.equal(data.readUInt32BE(20),1080)
  assert.equal(data[24],8);assert.equal(data[25],6);assert.ok(data.length<100000)
 }
})
