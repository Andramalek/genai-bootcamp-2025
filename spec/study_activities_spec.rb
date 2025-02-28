require 'spec_helper'

RSpec.describe 'Study Activities API' do
  describe 'GET /api/study_activities/:id' do
    it 'returns details of a specific study activity' do
      response = HTTParty.get("#{BASE_URL}/api/study_activities/1", headers: { 'Content-Type' => 'application/json' })
      expect(response.code).to eq(200)
      json = JSON.parse(response.body)
      expect(json).to include('id', 'study_session_id', 'group_id', 'created_at')
    end
  end
end 