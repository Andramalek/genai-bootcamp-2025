require 'spec_helper'

RSpec.describe 'Dashboard API' do
  describe 'GET /api/dashboard/last-study-session' do
    it 'returns the most recent study session with group name' do
      response = HTTParty.get("#{BASE_URL}/api/dashboard/last-study-session", headers: { 'Content-Type' => 'application/json' })
      expect(response.code).to eq(200)
      json = JSON.parse(response.body)
      expect(json).to include('id', 'group_id', 'created_at', 'study_activity_id', 'group_name')
    end
  end

  describe 'GET /api/dashboard/study-progress' do
    it 'returns study progress statistics' do
      response = HTTParty.get("#{BASE_URL}/api/dashboard/study-progress", headers: { 'Content-Type' => 'application/json' })
      expect(response.code).to eq(200)
      json = JSON.parse(response.body)
      expect(json).to include('total_words_studied', 'total_available_words')
    end
  end

  describe 'GET /api/dashboard/quick-stats' do
    it 'returns quick dashboard statistics' do
      response = HTTParty.get("#{BASE_URL}/api/dashboard/quick-stats", headers: { 'Content-Type' => 'application/json' })
      expect(response.code).to eq(200)
      json = JSON.parse(response.body)
      expect(json).to include('total_words', 'total_groups', 'words_mastered', 'recent_accuracy')
    end
  end
end 