% RUN_PIPELINE_VALIDATION.M
% MATLAB / Octave validation script for 4D Image Recognition pipeline outputs
% Loads pipeline JSON result(s) and produces comparative plots vs traditional/simple baselines.
%
% Usage:
%   1. Run the Python pipeline to generate a JSON results file (e.g. PIPELINE_ASSESSMENT_RESULTS.json)
%   2. In MATLAB/Octave, set resultsPath below or pass as arg: run_pipeline_validation('PIPELINE_ASSESSMENT_RESULTS.json')
%   3. Figures: credibility distribution, reverse image strength vs credibility, anomaly counts, brightness proxy outliers.
%
function run_pipeline_validation(resultsPath, baselinePath)
  if nargin < 1 || isempty(resultsPath); resultsPath = 'ENHANCED_RESULTS.json'; end
  if nargin < 2; baselinePath = ''; end
  if ~isfile(resultsPath); error('Results file not found: %s', resultsPath); end
  data = jsondecode(fileread(resultsPath));
  baseline = [];
  if ~isempty(baselinePath) && isfile(baselinePath)
    baseline = jsondecode(fileread(baselinePath));
  end

  if ~isfield(data,'osint_metadata')
    error('Result JSON missing osint_metadata field');
  end

  metas = data.osint_metadata;
  n = numel(metas);
  credibility = zeros(n,1);
  reverseStrength = zeros(n,1);
  hashDup = zeros(n,1);
  for i=1:n
    m = metas(i);
    if isfield(m,'credibility_score') && ~isempty(m.credibility_score)
      credibility(i) = m.credibility_score;
    end
    if isfield(m,'reverse_image_strength') && ~isempty(m.reverse_image_strength)
      reverseStrength(i) = m.reverse_image_strength;
    end
    if isfield(m,'hash_reuse_indicator') && strcmp(m.hash_reuse_indicator,'duplicate_in_session')
      hashDup(i) = 1;
    end
  end

  figure('Name','Credibility Distribution'); hold on;
  histogram(credibility, 'BinWidth', 0.1, 'FaceAlpha',0.6, 'DisplayName','Enhanced');
  if ~isempty(baseline) && isfield(baseline,'osint_metadata')
    bcred = zeros(numel(baseline.osint_metadata),1);
    for i=1:numel(baseline.osint_metadata)
      m = baseline.osint_metadata(i);
      if isfield(m,'credibility_score') && ~isempty(m.credibility_score); bcred(i)=m.credibility_score; end
    end
    histogram(bcred, 'BinWidth', 0.1, 'FaceAlpha',0.4, 'DisplayName','Baseline');
    legend show;
  end
  xlabel('Credibility Score'); ylabel('Frequency'); title('Metadata Credibility Distribution'); grid on; hold off;

  figure('Name','Reverse Strength vs Credibility'); hold on;
  scatter(credibility, reverseStrength, 40, 'filled','DisplayName','Enhanced');
  if ~isempty(baseline)
    % baseline may have reverse_image_strength absent -> zeros
    bstrength = zeros(size(credibility));
    if isfield(baseline,'osint_metadata')
      b_m = baseline.osint_metadata;
      bs = zeros(numel(b_m),1); bc=zeros(numel(b_m),1);
      for i=1:numel(b_m)
        mm = b_m(i);
        if isfield(mm,'credibility_score') && ~isempty(mm.credibility_score); bc(i)=mm.credibility_score; end
        if isfield(mm,'reverse_image_strength') && ~isempty(mm.reverse_image_strength); bs(i)=mm.reverse_image_strength; end
      end
      scatter(bc, bs, 40, 'filled','MarkerFaceAlpha',0.4,'DisplayName','Baseline');
    end
    legend show;
  end
  xlabel('Credibility'); ylabel('Reverse Image Strength'); title('Reverse Image Strength vs Credibility'); grid on; hold off;

  figure('Name','Hash Reuse Indicator');
  bar([sum(hashDup) n - sum(hashDup)]); set(gca,'XTickLabel',{'Duplicate','Unique'});
  ylabel('Count'); title('Hash Reuse Counts'); grid on;

  % Global anomaly summary if present
  if isfield(data,'osint_anomalies') && isfield(data.osint_anomalies,'global')
    g = data.osint_anomalies.global;
    fields = {'device_inconsistencies','timestamp_inconsistencies','isolated_gps','brightness_outliers','hash_duplicates'};
    counts = zeros(numel(fields),1);
    for k=1:numel(fields)
      f = fields{k};
      if isfield(g,f)
        arr = g.(f);
        if isstruct(arr)
          counts(k) = numel(arr);
        elseif iscell(arr)
          counts(k) = numel(arr);
        end
      end
    end
    figure('Name','Global Anomalies');
    bar(counts); set(gca,'XTick',1:numel(fields),'XTickLabel',fields); xtickangle(30);
    ylabel('Count'); title('Detected Global OSINT Anomalies'); grid on;
  end

  fprintf('Average credibility: %.3f\n', mean(credibility));
  fprintf('Average reverse image strength: %.3f\n', mean(reverseStrength));
end
