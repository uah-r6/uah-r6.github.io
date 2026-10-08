import {test} from 'node:test'
import assert from 'node:assert/strict'
import {existingRosterIdentity} from '../src/roster.ts'

test('assign an existing global identity by current username or case-insensitive alias',()=>{
 const players=[{id:10,username:'Nachofries_08',aliases:['OldName','Nachofries_08']},{id:11,username:'Other',aliases:['Other']}]
 for(const name of ['nachofries_08',' NACHOFRIES_08 ','oldname'])assert.equal(existingRosterIdentity(players,name).id,10)
 assert.equal(existingRosterIdentity(players,'new'),undefined)
 assert.equal(existingRosterIdentity(players,''),undefined)
})
test('ambiguous identities cannot be silently selected or merged',()=>{
 const players=[{id:1,username:'One',aliases:['Same']},{id:2,username:'Same',aliases:['Other']}]
 assert.equal(existingRosterIdentity(players,'same'),undefined)
 assert.equal(existingRosterIdentity(players,'one').id,1)
})
