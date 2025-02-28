require 'spec_helper'

RSpec.describe 'Reset API' do
  describe 'POST /api/reset_history' do
    it 'resets word review history' do
      response = HTTParty.post("#{BASE_URL}/api/reset_history", headers: { 'Content-Type' => 'application/json' })
      expect(response.code).to eq(200)
      json = JSON.parse(response.body)
      expect(json['message']).to eq("History reset successfully")
    end
  end

  describe 'POST /api/full_reset' do
    it 'performs a full reset' do
      response = HTTParty.post("#{BASE_URL}/api/full_reset", headers: { 'Content-Type' => 'application/json' })
      expect(response.code).to eq(200)
      json = JSON.parse(response.body)
      expect(json['message']).to eq("Full reset performed successfully")
    end
  end
end 