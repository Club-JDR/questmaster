const chai = require('chai');
const expect = chai.expect;
const toDaysMinutesSeconds = require('../utils/date');

describe('Test utils', () => {
    describe('toDaysMinutesSeconds', () => {
        it('should format seconds in days, hours, minutes and seconds', (done) => {
            expect(toDaysMinutesSeconds(60) == '1 minute');
            expect(toDaysMinutesSeconds(930) == '15 minutes, 30 seconds');
            expect(toDaysMinutesSeconds(703801) == '8 days, 3 hours, 30 minutes, 1 second');
            done();
        });
    });
});