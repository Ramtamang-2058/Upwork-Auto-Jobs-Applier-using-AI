/**
 * Content script - Runs on Upwork job pages
 * Extracts job data and adds "Generate Cover Letter" button
 */

// Configuration
// Point this at your running server. Localhost for development, or the
// URL of your deployed server (see docs/DEPLOYMENT.md).
const API_URL = 'http://localhost:5000';

// Create floating button
function createExtractButton() {
  try {
    console.log('🚀 Upwork AI Extension: Creating button...');

    // Check if button already exists
    if (document.getElementById('upwork-ai-button')) {
      console.log('✅ Button already exists');
      return;
    }

    // Wait for body to be ready
    if (!document.body) {
      console.log('⏳ Body not ready, waiting...');
      setTimeout(createExtractButton, 500);
      return;
    }

    const button = document.createElement('button');
    button.id = 'upwork-ai-button';
    button.className = 'upwork-ai-extract-btn';
    button.innerHTML = `
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor">
        <path d="M12 2L2 7l10 5 10-5-10-5z"></path>
        <path d="M2 17l10 5 10-5"></path>
        <path d="M2 12l10 5 10-5"></path>
      </svg>
      Generate Cover Letter
    `;

    button.addEventListener('click', extractAndSendJob);
    document.body.appendChild(button);

    console.log('✅ Button created successfully at bottom-right!');
    console.log('📍 Look for purple floating button at bottom-right corner');
  } catch (error) {
    console.error('❌ Error creating button:', error);
  }
}

// Extract job data from current page
function extractJobData() {
  console.log('🔍 Extracting job data from page...');

  try {
    // Get job title (from h1, h2, h3, or h4 in main content)
    let title = '';
    const titleElement = document.querySelector('h1') ||
                        document.querySelector('h2') ||
                        document.querySelector('h3') ||
                        document.querySelector('h4');

    if (titleElement) {
      title = titleElement.textContent.trim();
      console.log('✅ Found title:', title);
    } else {
      title = document.title.replace(' - Upwork', '').trim();
      console.log('📝 Using page title:', title);
    }

    // Extract job description from air3-card-section elements
    let description = '';

    // Get all air3-card-section elements (these contain job details)
    const sections = document.querySelectorAll('section.air3-card-section');
    console.log(`📦 Found ${sections.length} card sections`);

    let allSectionsText = '';
    sections.forEach((section, index) => {
      const sectionText = section.innerText.trim();
      if (sectionText.length > 20) {
        allSectionsText += sectionText + '\n\n';
        console.log(`📄 Section ${index + 1}: ${sectionText.substring(0, 50)}...`);
      }
    });

    description = allSectionsText.trim();

    // Fallback: Get text from main content area
    if (!description || description.length < 100) {
      console.log('⚠️ Trying fallback: main content extraction...');

      const mainContent = document.querySelector('main') ||
                         document.querySelector('[role="main"]') ||
                         document.querySelector('.job-details-content') ||
                         document.querySelector('div[class*="job-details"]');

      if (mainContent) {
        description = mainContent.innerText.substring(0, 3000).trim();
        console.log('✅ Extracted from main:', description.length, 'chars');
      }
    }

    // Last resort: Get entire body text
    if (!description || description.length < 100) {
      console.log('⚠️ Last resort: extracting from body...');
      description = document.body.innerText.substring(0, 3000).trim();
    }

    // Get current URL
    const link = window.location.href;

    // Build job data
    const jobData = {
      title: title,
      link: link,
      description: description,
      budget: '',
      experience_level: '',
      job_type: ''
    };

    console.log('✅ Final job data:', {
      title: jobData.title.substring(0, 60),
      descriptionLength: jobData.description.length,
      link: jobData.link
    });

    // Validate we have minimum required data
    if (!jobData.title || jobData.title.length < 5) {
      throw new Error('Could not find job title');
    }

    if (!jobData.description || jobData.description.length < 100) {
      throw new Error(`Description too short: ${jobData.description.length} chars`);
    }

    return jobData;

  } catch (error) {
    console.error('❌ Error extracting job data:', error);
    return null;
  }
}

// Helper function to find text by label
function findTextByLabel(labels) {
  for (const label of labels) {
    const elements = Array.from(document.querySelectorAll('*'));
    for (const el of elements) {
      if (el.textContent.includes(label) && el.nextSibling) {
        const text = el.nextSibling.textContent || el.parentElement.textContent;
        if (text && text.length > 0 && text.length < 100) {
          return text.trim();
        }
      }
    }
  }
  return '';
}

// Send job data to Python backend
async function extractAndSendJob() {
  const button = document.getElementById('upwork-ai-button');
  const originalText = button.innerHTML;

  // Show loading state
  button.disabled = true;
  button.innerHTML = `
    <div class="spinner"></div>
    Generating...
  `;

  try {
    // Check if we're on the apply page
    const isApplyPage = window.location.href.includes('/proposals/job/') &&
                        window.location.href.includes('/apply');

    let jobData;

    if (isApplyPage) {
      console.log('📝 On apply page - extracting available data or asking user...');

      // Try to extract what's available
      jobData = extractJobData();

      // If extraction fails on apply page, offer to paste
      if (!jobData || !jobData.description || jobData.description.length < 100) {
        showNotification('💡 On proposal page - please paste the job description, or go back to the job page first.', 'warning');

        // Offer option to manually paste description
        const description = prompt('Paste the full job description here (or click Cancel to go back to job page):');

        if (!description) {
          showNotification('ℹ️ Cancelled. Visit the job page first to use auto-extraction.', 'warning');
          return;
        }

        // Extract job ID from URL
        const jobIdMatch = window.location.href.match(/~(\d+)/);
        const jobId = jobIdMatch ? jobIdMatch[1] : '';

        jobData = {
          title: document.title.replace(' - Upwork', '').trim(),
          link: `https://www.upwork.com/jobs/~${jobId}/`,
          description: description,
          budget: '',
          experience_level: '',
          job_type: ''
        };
      }
    } else {
      // Regular job page extraction
      jobData = extractJobData();

      if (!jobData || !jobData.title) {
        showNotification('⚠️ Could not extract job data. Make sure you\'re on a job page.', 'warning');
        return;
      }
    }

    // Send to Python backend
    console.log('📤 Sending to backend:', API_URL);
    const response = await fetch(`${API_URL}/api/generate-cover-letter`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(jobData)
    });

    if (!response.ok) {
      throw new Error(`Server error: ${response.status}`);
    }

    const result = await response.json();
    console.log('✅ Response from backend:', result);

    if (result.cover_letter) {
      // Copy to clipboard
      await navigator.clipboard.writeText(result.cover_letter);

      // Show success
      showNotification('✅ Cover letter generated and copied to clipboard!', 'success');

      // Store in Chrome storage for popup access
      chrome.storage.local.set({
        latestJob: jobData,
        latestCoverLetter: result.cover_letter,
        timestamp: new Date().toISOString()
      });
    } else {
      throw new Error('No cover letter in response');
    }

  } catch (error) {
    console.error('❌ Error:', error);

    let errorMessage = 'Error generating cover letter.';
    if (error.message.includes('Failed to fetch')) {
      errorMessage = `⚠️ Cannot connect to server at ${API_URL}. Check if server is running and CORS is enabled.`;
    }

    showNotification(errorMessage, 'error');
  } finally {
    // Reset button
    button.disabled = false;
    button.innerHTML = originalText;
  }
}

// Show notification
function showNotification(message, type = 'info') {
  // Remove existing notification
  const existing = document.getElementById('upwork-ai-notification');
  if (existing) {
    existing.remove();
  }

  // Create notification
  const notification = document.createElement('div');
  notification.id = 'upwork-ai-notification';
  notification.className = `upwork-ai-notification ${type}`;
  notification.textContent = message;

  document.body.appendChild(notification);

  // Auto-remove after 5 seconds
  setTimeout(() => {
    notification.classList.add('fade-out');
    setTimeout(() => notification.remove(), 300);
  }, 5000);
}

// Initialize when page loads
console.log('🚀 Upwork Cover Letter Generator extension script loaded');
console.log('📍 Current URL:', window.location.href);

if (document.readyState === 'loading') {
  console.log('⏳ Document still loading, waiting for DOMContentLoaded...');
  document.addEventListener('DOMContentLoaded', () => {
    console.log('✅ DOMContentLoaded fired');
    createExtractButton();
  });
} else {
  console.log('✅ Document already loaded, creating button now');
  createExtractButton();
}

// Re-add button if user navigates (SPA behavior)
let lastUrl = location.href;
new MutationObserver(() => {
  const url = location.href;
  if (url !== lastUrl) {
    console.log('🔄 URL changed:', url);
    lastUrl = url;
    setTimeout(() => {
      console.log('🔄 Re-creating button after navigation');
      createExtractButton();
    }, 1000);
  }
}).observe(document, {subtree: true, childList: true});

console.log('✅ Extension initialized - Button should appear shortly!');
