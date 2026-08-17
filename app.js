// Simba Cement Kenya - Core Interactive Scripts

// Automatic system theme sync
(function initSystemTheme() {
  const media = window.matchMedia ? window.matchMedia('(prefers-color-scheme: dark)') : null;

  const applySystemTheme = () => {
    const dark = media && media.matches;
    document.documentElement.setAttribute('data-theme', dark ? 'dark' : 'light');
    document.documentElement.style.colorScheme = dark ? 'dark' : 'light';
    try { localStorage.removeItem('simba_theme'); } catch (e) {}
  };

  applySystemTheme();

  if (media) {
    if (typeof media.addEventListener === 'function') {
      media.addEventListener('change', applySystemTheme);
    } else if (typeof media.addListener === 'function') {
      media.addListener(applySystemTheme);
    }
  }
})();

document.addEventListener('DOMContentLoaded', () => {
  // Mobile Navigation Burger Menu Toggle
  const burger = document.getElementById('burger');
  const menu = document.getElementById('menu');
  if (burger && menu) {
    burger.addEventListener('click', () => {
      const open = menu.classList.toggle('open');
      burger.setAttribute('aria-expanded', String(open));
      burger.setAttribute('aria-label', open ? 'Close menu' : 'Open menu');
    });
    menu.querySelectorAll('a').forEach(a => a.addEventListener('click', () => {
      menu.classList.remove('open');
      if (burger) {
        burger.setAttribute('aria-expanded', 'false');
        burger.setAttribute('aria-label', 'Open menu');
      }
    }));
  }

  // Active Menu Link Highlighting
  const currentPath = window.location.pathname.split('/').pop() || 'index.html';
  document.querySelectorAll('.menu a').forEach(link => {
    const href = link.getAttribute('href');
    if (href === currentPath || (currentPath === '' && href === 'index.html')) {
      link.classList.add('active');
    }
  });

  // Quote Modal Logic
  const quoteModal = document.getElementById('quote-modal');
  const closeModalBtns = document.querySelectorAll('[data-close-modal]');
  const openQuoteBtns = document.querySelectorAll('[data-open-quote]');

  function updateModalFromBtn(btn) {
    const grade = btn.dataset.grade || '32.5R';
    const qty = btn.dataset.qty || '100';
    const projType = btn.dataset.type || '';
    const county = btn.dataset.county || '';
    const town = btn.dataset.town || '';

    const modalGrade = document.getElementById('modal-cement-type');
    const modalQty = document.getElementById('modal-qty');
    const modalProj = document.getElementById('modal-project');
    const modalCounty = document.getElementById('m-county');
    const modalTown = document.getElementById('m-town');

    if (modalGrade) {
      if (grade.includes('42.5N')) modalGrade.value = '42.5N (OPC)';
      else if (grade.includes('32.5R')) modalGrade.value = '32.5R (PPC)';
      else modalGrade.value = grade;
    }
    if (modalQty) modalQty.value = qty;
    if (modalProj && projType) modalProj.value = projType;
    if (modalCounty && county) modalCounty.value = county;
    if (modalTown && town) modalTown.value = town;

    const modalForm = document.getElementById('modal-quote-form');
    if (modalForm) {
      modalForm.querySelectorAll('input, select').forEach(input => {
        input.dispatchEvent(new Event('input', { bubbles: true }));
        input.dispatchEvent(new Event('change', { bubbles: true }));
      });
    }
  }

  openQuoteBtns.forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      updateModalFromBtn(btn);
      if (quoteModal) quoteModal.classList.add('open');
    });
  });

  closeModalBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      if (quoteModal) quoteModal.classList.remove('open');
    });
  });

  if (quoteModal) {
    quoteModal.addEventListener('click', (e) => {
      if (e.target === quoteModal) quoteModal.classList.remove('open');
    });
  }

  // Quotation System - Deep-Linked WhatsApp Generator
  function setupQuoteForm(formElementOrId, targetWaBtnId, summaryOutId) {
    const qForm = typeof formElementOrId === 'string' ? document.getElementById(formElementOrId) : formElementOrId;
    if (!qForm) return;

    const qtyInput = qForm.querySelector('[name="qty"]');
    const presets = qForm.querySelectorAll('.qty-btn');
    if (presets && qtyInput) {
      presets.forEach(pBtn => {
        pBtn.addEventListener('click', (e) => {
          e.preventDefault();
          presets.forEach(b => b.classList.remove('active'));
          pBtn.classList.add('active');
          qtyInput.value = pBtn.dataset.qty;
          triggerQuoteUpdate();
        });
      });
    }

    function triggerQuoteUpdate() {
      const typeRaw = qForm.querySelector('[name="cement_type"]')?.value || '32.5R (PPC)';
      const qtyRaw = qForm.querySelector('[name="qty"]')?.value || '100';
      const countyRaw = qForm.querySelector('[name="county"]')?.value || 'Nairobi';
      const townRaw = qForm.querySelector('[name="town"]')?.value || '';
      const projectRaw = qForm.querySelector('[name="project"]')?.value || 'Residential Construction';
      const deliveryRaw = qForm.querySelector('[name="delivery"]')?.value || 'Yes (Site Delivery Needed)';
      const nameRaw = qForm.querySelector('[name="name"]')?.value || '';
      const phoneRaw = qForm.querySelector('[name="phone"]')?.value || '';

      const qty = Math.max(1, parseInt(qtyRaw, 10) || 100);

      let pricePerBag = 550;
      let typeClean = typeRaw;
      if (typeRaw.includes('42.5N')) {
        pricePerBag = 680;
        typeClean = 'Simba 42.5N OPC';
      } else if (typeRaw.includes('32.5R')) {
        pricePerBag = 550;
        typeClean = 'Simba 32.5R PPC';
      } else if (typeRaw.toLowerCase().includes('mixed')) {
        pricePerBag = 615;
        typeClean = 'Mixed Order (32.5R PPC & 42.5N OPC)';
      }

      const totalCost = qty * pricePerBag;

      // Location Formatting
      const countyClean = countyRaw.trim();
      const townClean = townRaw.trim();
      let locationStr = countyClean;
      if (townClean) {
        if (townClean.toLowerCase().includes(countyClean.toLowerCase())) {
          locationStr = townClean;
        } else {
          locationStr = `${townClean}, ${countyClean} County`;
        }
      } else if (!countyClean.toLowerCase().includes('county')) {
        locationStr = `${countyClean} County`;
      }

      // Update Summary Element
      const summaryOut = (targetWaBtnId ? document.getElementById(summaryOutId) : null) || 
                         qForm.querySelector('[id$="-summary"]') || 
                         qForm.querySelector('.quote-summary');
      if (summaryOut) {
        summaryOut.innerHTML = `<strong>${qty.toLocaleString('en-KE')} bags</strong> of ${typeClean} to <strong>${locationStr}</strong>. Indicative estimate: <strong>KSh ${totalCost.toLocaleString('en-KE')}</strong>.`;
      }

      // Format Deep-Linked WhatsApp Message
      let msg = `Hello Simba Cement Sales Kenya 👋\n\n`;
      msg += `I would like to request an official quotation for my construction project:\n\n`;
      msg += `🏗️ Product Grade: ${typeClean}\n`;
      msg += `📦 Quantity: ${qty.toLocaleString('en-KE')} bags (50kg)\n`;
      msg += `📍 Delivery Location: ${locationStr}\n`;
      msg += `🚚 Site Delivery: ${deliveryRaw}\n`;
      msg += `🏠 Project Type: ${projectRaw}\n`;
      msg += `💰 Indicative Cost: KSh ${totalCost.toLocaleString('en-KE')} (at KSh ${pricePerBag}/bag)\n`;
      if (nameRaw.trim()) msg += `👤 Contact Name: ${nameRaw.trim()}\n`;
      if (phoneRaw.trim()) msg += `📞 Phone Number: ${phoneRaw.trim()}\n`;
      msg += `\nPlease confirm current factory pricing, stock availability, and delivery dispatch schedule. Thank you!`;

      // Construct Deep-Link URL (wa.me opens directly in native WhatsApp on mobile & WhatsApp Web/Desktop)
      const waUrl = `https://wa.me/254754131137?text=${encodeURIComponent(msg)}`;

      // Update Target WhatsApp Button
      const waBtn = (targetWaBtnId ? document.getElementById(targetWaBtnId) : null) || 
                    qForm.querySelector('.btn-whatsapp');
      if (waBtn) {
        waBtn.setAttribute('href', waUrl);
      }

      return waUrl;
    }

    qForm.querySelectorAll('input, select, textarea').forEach(input => {
      input.addEventListener('input', triggerQuoteUpdate);
      input.addEventListener('change', triggerQuoteUpdate);
    });

    qForm.addEventListener('submit', (e) => {
      e.preventDefault();
      const waUrl = triggerQuoteUpdate();
      if (waUrl) {
        window.open(waUrl, '_blank');
      }
    });

    const waBtn = (targetWaBtnId ? document.getElementById(targetWaBtnId) : null) || 
                  qForm.querySelector('.btn-whatsapp');
    if (waBtn) {
      waBtn.addEventListener('click', (e) => {
        const waUrl = triggerQuoteUpdate();
        waBtn.setAttribute('href', waUrl);
      });
    }

    triggerQuoteUpdate();
  }

  // Initialize specific and all general quote forms
  setupQuoteForm('quote-card-form', 'quote-wa-btn', 'quote-summary');
  setupQuoteForm('modal-quote-form', 'modal-wa-btn', 'modal-summary');
  document.querySelectorAll('.quote-form').forEach(form => {
    if (form.id !== 'quote-card-form' && form.id !== 'modal-quote-form') {
      setupQuoteForm(form);
    }
  });

  // Upgraded Engineering Cement & Concrete Calculator
  const calcForm = document.getElementById('calc-form');
  const calcOut = document.getElementById('calc-result');

  if (calcForm && calcOut) {
    const calcType = document.getElementById('calc-type');
    const thickWrap = document.getElementById('calc-thickness-wrap');

    if (calcType && thickWrap) {
      calcType.addEventListener('change', () => {
        const val = calcType.value;
        if (val === 'slab' || val === 'foundation' || val === 'column_beam') {
          thickWrap.style.display = 'block';
        } else {
          thickWrap.style.display = 'none';
        }
      });
    }

    calcForm.addEventListener('submit', (e) => {
      e.preventDefault();

      const type = document.getElementById('calc-type').value;
      const length = parseFloat(document.getElementById('calc-length').value) || 0;
      const width = parseFloat(document.getElementById('calc-width').value) || 0;
      const thickness = parseFloat(document.getElementById('calc-thickness')?.value || 0.15) || 0.15;

      if (length <= 0 || width <= 0) {
        calcOut.innerHTML = '<p class="text-amber">Please enter valid positive dimensions.</p>';
        return;
      }

      let bags = 0;
      let sandTonnes = 0;
      let ballastTonnes = 0;
      let suggestedGrade = '32.5R';
      let gradeDesc = '32.5R Portland Pozzolana Cement (PPC)';
      let pricePerBag = 550;
      let unitLabel = '';

      if (type === 'walling') {
        const area = length * width; // m²
        bags = Math.ceil(area * 0.30 * 1.05); // 5% wastage
        sandTonnes = (area * 0.04).toFixed(1);
        suggestedGrade = '32.5R';
        gradeDesc = 'Simba 32.5R PPC (Best for smooth mortar bond & masonry)';
        pricePerBag = 550;
        unitLabel = `${area.toFixed(1)} m² of block/stone walling`;
      } else if (type === 'plaster') {
        const area = length * width; // m²
        bags = Math.ceil(area * 0.18 * 1.05);
        sandTonnes = (area * 0.025).toFixed(1);
        suggestedGrade = '32.5R';
        gradeDesc = 'Simba 32.5R PPC (Superior workability, low cracking)';
        pricePerBag = 550;
        unitLabel = `${area.toFixed(1)} m² of plastering/rendering (15mm thickness)`;
      } else if (type === 'screed') {
        const area = length * width; // m²
        bags = Math.ceil(area * 0.22 * 1.05);
        sandTonnes = (area * 0.035).toFixed(1);
        suggestedGrade = '32.5R';
        gradeDesc = 'Simba 32.5R PPC';
        pricePerBag = 550;
        unitLabel = `${area.toFixed(1)} m² of floor screed (25mm)`;
      } else if (type === 'slab') {
        const volume = length * width * thickness; // m³
        bags = Math.ceil(volume * 7.0 * 1.07); // 7% wastage
        sandTonnes = (volume * 0.75).toFixed(1);
        ballastTonnes = (volume * 1.15).toFixed(1);
        suggestedGrade = '42.5N';
        gradeDesc = 'Simba 42.5N OPC (High strength for reinforced floor slabs)';
        pricePerBag = 680;
        unitLabel = `${volume.toFixed(2)} m³ concrete slab (Mix 1:2:4 Class 20)`;
      } else if (type === 'foundation') {
        const volume = length * width * thickness; // m³
        bags = Math.ceil(volume * 6.2 * 1.07);
        sandTonnes = (volume * 0.8).toFixed(1);
        ballastTonnes = (volume * 1.2).toFixed(1);
        suggestedGrade = '42.5N';
        gradeDesc = 'Simba 42.5N OPC (Heavy load-bearing strip foundation & footings)';
        pricePerBag = 680;
        unitLabel = `${volume.toFixed(2)} m³ concrete foundation footing`;
      } else if (type === 'column_beam') {
        const volume = length * width * thickness; // m³
        bags = Math.ceil(volume * 8.2 * 1.07);
        sandTonnes = (volume * 0.7).toFixed(1);
        ballastTonnes = (volume * 1.1).toFixed(1);
        suggestedGrade = '42.5N';
        gradeDesc = 'Simba 42.5N OPC (High early strength gain for structural columns & beams)';
        pricePerBag = 680;
        unitLabel = `${volume.toFixed(2)} m³ concrete columns & structural beams`;
      } else if (type === 'blockwork') {
        const area = length * width;
        bags = Math.ceil(area * 0.35 * 1.05);
        sandTonnes = (area * 0.05).toFixed(1);
        suggestedGrade = '32.5R';
        gradeDesc = 'Simba 32.5R PPC (Block laying & joint mortar)';
        pricePerBag = 550;
        unitLabel = `${area.toFixed(1)} m² concrete block laying`;
      }

      const totalCost = bags * pricePerBag;
      const sandWheelbarrows = Math.round(parseFloat(sandTonnes) * 18);
      const ballastWheelbarrows = ballastTonnes ? Math.round(parseFloat(ballastTonnes) * 18) : 0;

      calcOut.innerHTML = `
        <div class="calc-outputs">
          <div>
            <span class="eyebrow" style="color:var(--amber)">Estimated Material Requirements</span>
            <h3 style="color:#ffffff;margin-top:.2rem">${bags} Bags of Simba Cement (${suggestedGrade})</h3>
            <p style="font-size:.9rem;color:#cbd5e1;margin-bottom:1rem">${unitLabel}</p>
          </div>
          
          <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:.8rem;">
            <div class="calc-stat">
              <div class="calc-stat-val">${bags}</div>
              <div class="calc-stat-lbl">Cement Bags (50kg)</div>
            </div>
            <div class="calc-stat">
              <div class="calc-stat-val">${sandTonnes}t</div>
              <div class="calc-stat-lbl">Clean Sand (~${sandWheelbarrows} w/barrows)</div>
            </div>
            ${ballastTonnes ? `
            <div class="calc-stat">
              <div class="calc-stat-val">${ballastTonnes}t</div>
              <div class="calc-stat-lbl">Ballast / Gravel (~${ballastWheelbarrows} w/barrows)</div>
            </div>` : ''}
          </div>

          <div style="background:rgba(255,255,255,.08);padding:1rem;border-radius:8px;border:1px solid rgba(255,255,255,.12);margin-top:.5rem;">
            <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:.5rem;">
              <div>
                <strong style="color:var(--amber);display:block;font-size:1.1rem">Estimated Cement Cost: KSh ${totalCost.toLocaleString('en-KE')}</strong>
                <span style="font-size:.8rem;color:#cbd5e1">Based on indicative rate of KSh ${pricePerBag} per bag.</span>
              </div>
              <button type="button" class="btn btn-primary btn-sm" data-open-quote data-grade="${suggestedGrade}" data-qty="${bags}" data-type="${type}">
                Get Quotation for ${bags} Bags
              </button>
            </div>
          </div>

          <p class="calc-disclaimer">
            <strong>Recommended Grade:</strong> ${gradeDesc}.<br>
            <em>Engineering Note:</em> Calculations include a standard 5-7% site spillage and compaction allowance. Structural concrete specifications should be verified against structural engineer drawings.
          </p>
        </div>
      `;

      // Re-bind quote modal triggers on newly rendered button
      calcOut.querySelectorAll('[data-open-quote]').forEach(btn => {
        btn.addEventListener('click', () => {
          const modalGrade = document.getElementById('modal-cement-type');
          const modalQty = document.getElementById('modal-qty');
          if (modalGrade) modalGrade.value = btn.dataset.grade;
          if (modalQty) modalQty.value = btn.dataset.qty;
          if (quoteModal) quoteModal.classList.add('open');
        });
      });
    });
  }

  // Gallery Filters
  const filterBtns = document.querySelectorAll('[data-gallery-filter]');
  const galleryItems = document.querySelectorAll('[data-gallery-category]');

  if (filterBtns.length > 0 && galleryItems.length > 0) {
    filterBtns.forEach(btn => {
      btn.addEventListener('click', () => {
        filterBtns.forEach(b => b.classList.remove('active', 'btn-primary'));
        filterBtns.forEach(b => b.classList.add('btn-outline'));
        btn.classList.add('active', 'btn-primary');
        btn.classList.remove('btn-outline');

        const cat = btn.dataset.galleryFilter;
        galleryItems.forEach(item => {
          if (cat === 'all' || item.dataset.galleryCategory === cat) {
            item.style.display = 'block';
          } else {
            item.style.display = 'none';
          }
        });
      });
    });
  }

  // FAQ Details Accordion Auto Close others
  document.querySelectorAll('details').forEach(detail => {
    detail.addEventListener('toggle', () => {
      if (detail.open) {
        document.querySelectorAll('details').forEach(other => {
          if (other !== detail && other.open) other.open = false;
        });
      }
    });
  });
  // Start the cache early so future mobile visits load from local storage.
  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('./sw.js').catch(() => {});
  }
});
