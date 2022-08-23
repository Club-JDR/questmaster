const chai = require('chai');
const chaiHttp = require('chai-http');
const expect = chai.expect;

process.env.QUESTMASTER_PORT = 8888; // Use specific port for testing
const app = require('../app');

chai.use(chaiHttp);

describe('Test API endpoints', () => {
    describe('GET /health', () => {
        it('/health should send specific JSON', (done) => {
            chai.request(app)
                .get('/health')
                .end((err, res) => {
                    expect(res).to.have.status(200);
                    expect(res).to.be.json;
                    expect(res.body).to.include.all.keys('title', 'version', 'status', 'uptime', 'date');
                    done();
                });
        });
    });
});