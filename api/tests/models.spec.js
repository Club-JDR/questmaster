const mongoose = require('mongoose');
const chai = require('chai');
const expect = chai.expect;
const User = require('../models/user');
const Game = require('../models/game');

const users = [
    new User({}),
    new User({
        id: 'bob',
        isDM: false,
        pic: 'http://localhost/avatar.png'
    }),
    new User({
        id: 'bob#0001',
        isDM: false,
        pic: 'http://localhost/avatar.png'
    })
]

const games = [
    new Game({}),
    new Game({
        name: 'Lost Mines of Phandelver',
        type: 'campaign',
        dm: 'Notsag#0001',
        system: '5e',
        pitch: 'Explore this introductory adventure to get started playing the world’s greatest roleplaying game.',
        channel: 'lost-mine-of-phandelver',
        role: 'PJ_Phandelver'
    })
]

describe('Test models', () => {
    describe('User', () => {
        it('should have required fields set', (done) => {
            users[0].validate((err) => {
                expect(err.errors.id.kind == 'required');
                expect(err.errors.isDM.kind == 'required');
                expect(err.errors.pic.kind == 'required');
                done();
            });
        });
        it('should have an valid id', (done) => {
            users[1].validate((err) => {
                expect(err.errors.id.kind == 'regexp');
                done();
            });
        });
        it('should be ok when all reqquired is set and valid', (done) => {
            users[2].validate((err) => {
                expect(err).to.be.null;
                done();
            });
        });
    });

    describe('Game', () => {
        it('should have required fields set and good default values', (done) => {
            games[0].validate((err) => {
                expect(err.errors.name.kind == 'required');
                expect(games[0].type == 'oneshot');
                expect(err.errors.dm.kind == 'required');
                expect(err.errors.system.kind == 'required');
                expect(err.errors.pitch.kind == 'required');
                expect(games[0].restriction == 'all');
                expect(games[0].pregen == false);
                expect(games[0].selection == false);
                expect(games[0].partySize == 4);
                expect(err.errors.channel.kind == 'required');
                expect(err.errors.role.kind == 'required');
                done();
            });
        });
        it('should be ok when all required is set and valid', (done) => {
            games[1].validate((err) => {
                expect(err).to.be.null;
                done();
            });
        });
    });
});